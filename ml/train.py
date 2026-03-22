"""
ScreenSense — Main training script.

Usage:
    cd ml/
    python train.py

Outputs saved to ml/checkpoints/ and ml/results/.
"""
import os
import sys
import time
import json
from pathlib import Path

import torch
import torch.optim as optim

import config
from dataset import get_dataloaders
from model import ScreenSenseNet
from losses import SaliencyLoss
from utils import (
    set_seed,
    get_device,
    save_checkpoint,
    load_checkpoint,
    plot_training_curves,
)


# ── Setup ─────────────────────────────────────────────────────────────────────

set_seed(config.SEED)
device = get_device()

Path(config.CHECKPOINT_DIR).mkdir(parents=True, exist_ok=True)
Path(config.RESULTS_DIR).mkdir(parents=True, exist_ok=True)

BEST_CKPT = os.path.join(config.CHECKPOINT_DIR, "best_model.pth")
LAST_CKPT = os.path.join(config.CHECKPOINT_DIR, "last_model.pth")


# ── Helpers ───────────────────────────────────────────────────────────────────

def train_one_epoch(model, loader, criterion, optimizer, scaler, epoch):
    model.train()
    total_loss = 0.0
    component_sums = {"kl": 0.0, "cc": 0.0, "bce": 0.0}
    n_batches = len(loader)

    for batch_idx, (images, maps) in enumerate(loader):
        images = images.to(device, non_blocking=True)
        maps   = maps.to(device,   non_blocking=True)

        optimizer.zero_grad(set_to_none=True)

        if config.USE_AMP:
            with torch.cuda.amp.autocast():
                preds = model(images)
                loss, components = criterion(preds, maps)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()
        else:
            preds = model(images)
            loss, components = criterion(preds, maps)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

        total_loss += loss.item()
        for k, v in components.items():
            component_sums[k] += v

        if (batch_idx + 1) % config.LOG_EVERY_N_BATCHES == 0:
            avg = total_loss / (batch_idx + 1)
            print(
                f"  Epoch {epoch:02d} [{batch_idx+1:04d}/{n_batches}]"
                f"  loss={avg:.4f}"
                f"  kl={component_sums['kl']/(batch_idx+1):.4f}"
                f"  cc={component_sums['cc']/(batch_idx+1):.4f}"
                f"  bce={component_sums['bce']/(batch_idx+1):.4f}"
            )

    return total_loss / n_batches


@torch.no_grad()
def validate(model, loader, criterion):
    model.eval()
    total_loss = 0.0

    for images, maps in loader:
        images = images.to(device, non_blocking=True)
        maps   = maps.to(device,   non_blocking=True)

        if config.USE_AMP:
            with torch.cuda.amp.autocast():
                preds = model(images)
                loss, _ = criterion(preds, maps)
        else:
            preds = model(images)
            loss, _ = criterion(preds, maps)

        total_loss += loss.item()

    torch.cuda.empty_cache()
    return total_loss / len(loader)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print("  ScreenSense — Training")
    print("=" * 60)

    # Data
    train_loader, val_loader = get_dataloaders(
        batch_size=config.BATCH_SIZE,
        num_workers=config.NUM_WORKERS,
    )

    # Model
    model = ScreenSenseNet(pretrained=True).to(device)
    model.count_params()

    # Freeze encoder for the first N epochs
    if config.FREEZE_ENCODER_EPOCHS > 0:
        model.freeze_encoder()

    # Loss
    criterion = SaliencyLoss(
        kl_weight=config.KL_WEIGHT,
        cc_weight=config.CC_WEIGHT,
        bce_weight=config.BCE_WEIGHT,
    )

    # Optimizer — separate LRs for encoder vs decoder
    encoder_params = list(model.encoder.parameters())
    decoder_params = [p for n, p in model.named_parameters()
                      if not n.startswith("encoder")]
    optimizer = optim.Adam([
        {"params": encoder_params, "lr": config.LEARNING_RATE_ENCODER},
        {"params": decoder_params, "lr": config.LEARNING_RATE_DECODER},
    ], weight_decay=config.WEIGHT_DECAY)

    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=config.LR_FACTOR,
        patience=config.LR_PATIENCE, verbose=True,
    )

    scaler = torch.cuda.amp.GradScaler(enabled=config.USE_AMP)

    # ── Training loop ────────────────────────────────────────────────────

    train_losses, val_losses = [], []
    best_val_loss   = float("inf")
    epochs_no_improve = 0
    start_time      = time.time()

    for epoch in range(1, config.EPOCHS + 1):
        epoch_start = time.time()

        # Unfreeze encoder after N epochs
        if epoch == config.FREEZE_ENCODER_EPOCHS + 1:
            model.unfreeze_encoder()
            # Also activate encoder's optimizer group
            optimizer.param_groups[0]["lr"] = config.LEARNING_RATE_ENCODER
            print(f"  → Encoder unfrozen at epoch {epoch}")

        print(f"\nEpoch {epoch}/{config.EPOCHS}")

        train_loss = train_one_epoch(model, train_loader, criterion, optimizer, scaler, epoch)
        val_loss   = validate(model, val_loader, criterion)

        scheduler.step(val_loss)

        train_losses.append(train_loss)
        val_losses.append(val_loss)

        epoch_time = time.time() - epoch_start
        print(
            f"  → train_loss={train_loss:.4f}  val_loss={val_loss:.4f}"
            f"  [{epoch_time:.0f}s]"
        )

        # Checkpoint
        state = {
            "epoch":           epoch,
            "model_state":     model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "val_loss":        val_loss,
            "best_val_loss":   best_val_loss,
            "train_losses":    train_losses,
            "val_losses":      val_losses,
        }
        save_checkpoint(state, LAST_CKPT)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            epochs_no_improve = 0
            save_checkpoint(state, BEST_CKPT)
            print(f"  ✓ New best val_loss={best_val_loss:.4f}  checkpoint saved.")
        else:
            epochs_no_improve += 1
            print(f"  No improvement ({epochs_no_improve}/{config.EARLY_STOPPING_PATIENCE})")

        if epochs_no_improve >= config.EARLY_STOPPING_PATIENCE:
            print(f"\nEarly stopping triggered at epoch {epoch}.")
            break

    # ── Post-training ────────────────────────────────────────────────────

    total_time = time.time() - start_time
    print(f"\nTraining complete in {total_time/60:.1f} min")
    print(f"Best val loss: {best_val_loss:.4f}")

    # Save training curves
    plot_training_curves(
        train_losses, val_losses,
        save_path=os.path.join(config.RESULTS_DIR, "training_curves.png"),
    )

    # Save history JSON for reference
    history = {"train_loss": train_losses, "val_loss": val_losses}
    with open(os.path.join(config.RESULTS_DIR, "training_history.json"), "w") as f:
        json.dump(history, f, indent=2)

    # Copy best weights to the backend model directory
    import shutil
    backend_model_dir = os.path.join(
        os.path.dirname(config.ROOT_DIR), "screensense", "backend", "model"
    )
    backend_model_dir = os.path.join(config.ROOT_DIR, "backend", "model")
    if os.path.exists(backend_model_dir):
        dest = os.path.join(backend_model_dir, "best_model.pth")
        shutil.copy(BEST_CKPT, dest)
        print(f"Copied best_model.pth → {dest}")

    print("\nAll done. Run `python evaluate.py` next.")


if __name__ == "__main__":
    main()
