"""
Shared utilities: seeding, checkpointing, visualisation helpers.
"""
import os
import random
import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")   # headless
import matplotlib.pyplot as plt
from pathlib import Path


# ── Reproducibility ───────────────────────────────────────────────────────────

def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark     = False


# ── Checkpoint helpers ────────────────────────────────────────────────────────

def save_checkpoint(state: dict, path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    torch.save(state, path)


def load_checkpoint(path: str, model, optimizer=None, device="cpu"):
    ckpt = torch.load(path, map_location=device)
    model.load_state_dict(ckpt["model_state"])
    if optimizer and "optimizer_state" in ckpt:
        optimizer.load_state_dict(ckpt["optimizer_state"])
    epoch = ckpt.get("epoch", 0)
    best_val_loss = ckpt.get("best_val_loss", float("inf"))
    print(f"Loaded checkpoint from epoch {epoch}  |  best val loss: {best_val_loss:.4f}")
    return epoch, best_val_loss


# ── Training curve ────────────────────────────────────────────────────────────

def plot_training_curves(train_losses: list, val_losses: list, save_path: str):
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10, 5))
    plt.plot(train_losses, label="Train loss", linewidth=2)
    plt.plot(val_losses,   label="Val loss",   linewidth=2)
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title("Training Curves — ScreenSense")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"Saved training curves → {save_path}")


# ── Saliency map colourisation ────────────────────────────────────────────────

def apply_colormap(sal_map: np.ndarray, cmap: str = "jet") -> np.ndarray:
    """
    Convert a (H, W) float saliency map in [0, 1] to an (H, W, 3) uint8 RGB image.
    """
    cm = plt.get_cmap(cmap)
    colored = cm(sal_map)[:, :, :3]          # drop alpha
    return (colored * 255).astype(np.uint8)


def overlay_heatmap(
    image_rgb: np.ndarray,
    sal_map:   np.ndarray,
    alpha:     float = 0.4,
    cmap:      str   = "jet",
) -> np.ndarray:
    """
    Blend a coloured heatmap onto the original image.

    image_rgb : (H, W, 3) uint8
    sal_map   : (H, W)    float32 in [0, 1]
    Returns     (H, W, 3) uint8 blended image
    """
    colored = apply_colormap(sal_map, cmap).astype(np.float32)
    base    = image_rgb.astype(np.float32)
    blended = (1 - alpha) * base + alpha * colored
    return np.clip(blended, 0, 255).astype(np.uint8)


# ── Denormalise image tensor ──────────────────────────────────────────────────

_MEAN = np.array([0.485, 0.456, 0.406])
_STD  = np.array([0.229, 0.224, 0.225])


def tensor_to_numpy_image(tensor: torch.Tensor) -> np.ndarray:
    """
    Convert an ImageNet-normalised (C, H, W) tensor to a (H, W, 3) uint8 array.
    """
    img = tensor.cpu().numpy().transpose(1, 2, 0)
    img = (img * _STD + _MEAN).clip(0, 1)
    return (img * 255).astype(np.uint8)


# ── Device helper ─────────────────────────────────────────────────────────────

def get_device() -> torch.device:
    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        mem  = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"GPU: {name}  ({mem:.1f} GB)")
        return torch.device("cuda")
    print("No GPU found — using CPU.")
    return torch.device("cpu")
