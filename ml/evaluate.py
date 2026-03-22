"""
ScreenSense — Evaluation script.

Loads the best trained model and runs all 5 standard saliency metrics
over the entire validation set, then generates a comparison grid.

Usage:
    cd ml/
    python evaluate.py
"""
import os
import sys
import json
import numpy as np
from pathlib import Path
from tqdm import tqdm

import torch
from torch.utils.data import DataLoader
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config
from model import ScreenSenseNet
from dataset import SaliconDataset
from metrics import compute_all_metrics, _normalise
from utils import get_device, tensor_to_numpy_image, apply_colormap

# ── Setup ─────────────────────────────────────────────────────────────────────

device  = get_device()
BEST_CKPT = os.path.join(config.CHECKPOINT_DIR, "best_model.pth")
RESULTS   = config.RESULTS_DIR
Path(RESULTS).mkdir(parents=True, exist_ok=True)


# ── Load model ────────────────────────────────────────────────────────────────

def load_model(ckpt_path: str) -> ScreenSenseNet:
    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(
            f"Checkpoint not found: {ckpt_path}\n"
            "Run `python train.py` first."
        )
    model = ScreenSenseNet(pretrained=False).to(device)
    ckpt  = torch.load(ckpt_path, map_location=device)
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    epoch = ckpt.get("epoch", "?")
    loss  = ckpt.get("best_val_loss", float("nan"))
    print(f"Loaded checkpoint  epoch={epoch}  best_val_loss={loss:.4f}")
    return model


# ── Inference helper ──────────────────────────────────────────────────────────

@torch.no_grad()
def predict_batch(model, images: torch.Tensor) -> np.ndarray:
    """Return predicted saliency maps as numpy (B, H, W) in [0, 1]."""
    if config.USE_AMP:
        with torch.cuda.amp.autocast():
            out = model(images.to(device))
    else:
        out = model(images.to(device))
    return out.squeeze(1).cpu().numpy()   # (B, H, W)


# ── Evaluation loop ───────────────────────────────────────────────────────────

def evaluate():
    print("\n" + "=" * 60)
    print("  ScreenSense — Evaluation")
    print("=" * 60)

    model = load_model(BEST_CKPT)

    # SALICON val set — we need both continuous maps AND fixation maps
    # If fixation maps are available, put them in data/val/fixations/
    # otherwise we threshold the GT map to create a binary proxy
    val_dataset = SaliconDataset(
        config.VAL_IMG_DIR, config.VAL_MAP_DIR, split="val"
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=config.BATCH_SIZE,
        shuffle=False,
        num_workers=config.NUM_WORKERS,
        pin_memory=True,
    )

    all_metrics = {k: [] for k in ["AUC-Judd", "CC", "NSS", "SIM", "KL-Div"]}

    print(f"\nRunning inference on {len(val_dataset)} validation images …")
    for images, gt_maps in tqdm(val_loader, unit="batch"):
        preds = predict_batch(model, images)      # (B, H, W)
        gt    = gt_maps.squeeze(1).numpy()        # (B, H, W)

        for i in range(len(preds)):
            pred_i = _normalise(preds[i])
            gt_i   = _normalise(gt[i])
            # Binary fixation map — threshold at 80th percentile of GT map
            fix_i  = (gt_i >= np.percentile(gt_i[gt_i > 0], 80)).astype(np.float32) \
                     if gt_i.max() > 0 else np.zeros_like(gt_i)

            m = compute_all_metrics(pred_i, gt_i, fix_i)
            for k, v in m.items():
                if not np.isnan(v):
                    all_metrics[k].append(v)

        torch.cuda.empty_cache()

    # ── Print results table ────────────────────────────────────────────────

    print("\n" + "=" * 50)
    print(f"  {'Metric':<15} {'Mean':>10}  {'Std':>10}")
    print("  " + "-" * 38)
    results_dict = {}
    for metric, values in all_metrics.items():
        mean = float(np.mean(values))
        std  = float(np.std(values))
        results_dict[metric] = {"mean": mean, "std": std}
        # Higher is better for AUC, CC, NSS, SIM; lower for KL-Div
        arrow = "↑" if metric != "KL-Div" else "↓"
        print(f"  {metric:<15} {mean:>10.4f}  {std:>10.4f}  {arrow}")
    print("=" * 50)

    with open(os.path.join(RESULTS, "eval_metrics.json"), "w") as f:
        json.dump(results_dict, f, indent=2)
    print(f"\nMetrics saved → {RESULTS}/eval_metrics.json")

    return model, val_dataset


# ── Comparison grid ───────────────────────────────────────────────────────────

def generate_comparison_grid(model, dataset, n_examples: int = 12):
    """Save a grid: Original | GT Saliency | Predicted Saliency."""
    indices = np.random.choice(len(dataset), size=min(n_examples, len(dataset)), replace=False)
    n_cols  = 3
    n_rows  = len(indices)

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, n_rows * 3))
    fig.suptitle("ScreenSense — Predictions vs Ground Truth", fontsize=14, fontweight="bold")

    col_titles = ["Original Image", "Ground Truth Saliency", "Predicted Saliency"]
    for ax, title in zip(axes[0], col_titles):
        ax.set_title(title, fontsize=11)

    for row, idx in enumerate(indices):
        # Get raw pair (PIL images, not normalised)
        raw_img, raw_map = dataset.get_raw_pair(idx)

        # Model inference on the normalised tensor
        img_tensor, _ = dataset[idx]
        img_tensor = img_tensor.unsqueeze(0)

        with torch.no_grad():
            if config.USE_AMP:
                with torch.cuda.amp.autocast():
                    pred = model(img_tensor.to(device))
            else:
                pred = model(img_tensor.to(device))

        pred_map = pred.squeeze().cpu().numpy()
        pred_map = _normalise(pred_map)
        gt_map   = _normalise(np.array(raw_map, dtype=np.float32) / 255.0)

        axes[row, 0].imshow(raw_img)
        axes[row, 1].imshow(gt_map,   cmap="jet", vmin=0, vmax=1)
        axes[row, 2].imshow(pred_map, cmap="jet", vmin=0, vmax=1)

        for ax in axes[row]:
            ax.axis("off")

    plt.tight_layout()
    save_path = os.path.join(RESULTS, "comparison_grid.png")
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Comparison grid saved → {save_path}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    model, dataset = evaluate()
    generate_comparison_grid(model, dataset, n_examples=12)
    print("\nEvaluation complete.")
