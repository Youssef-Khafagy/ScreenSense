"""
Generate additional visualisations after training/evaluation.

  - Training curves (re-plots from saved history JSON)
  - Attention heatmap samples (15 diverse examples)
  - Saliency intensity histogram
"""
import os
import json
import numpy as np
from pathlib import Path
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

import config
from model import ScreenSenseNet
from dataset import SaliconDataset
from utils import get_device, apply_colormap, _normalise, tensor_to_numpy_image

RESULTS = config.RESULTS_DIR
CKPT    = os.path.join(config.CHECKPOINT_DIR, "best_model.pth")
device  = get_device()


def plot_curves_from_json():
    history_path = os.path.join(RESULTS, "training_history.json")
    if not os.path.exists(history_path):
        print("No training_history.json found. Skipping curve plot.")
        return
    with open(history_path) as f:
        history = json.load(f)

    plt.figure(figsize=(10, 5))
    plt.plot(history["train_loss"], "b-o", label="Train", markersize=4)
    plt.plot(history["val_loss"],   "r-o", label="Val",   markersize=4)
    plt.xlabel("Epoch"); plt.ylabel("Loss")
    plt.title("ScreenSense — Training Curves")
    plt.legend(); plt.grid(True, alpha=0.3)
    plt.tight_layout()
    out = os.path.join(RESULTS, "training_curves_repot.png")
    plt.savefig(out, dpi=150); plt.close()
    print(f"Curve plot → {out}")


def attention_samples(n: int = 15):
    if not os.path.exists(CKPT):
        print("No checkpoint found. Skipping sample generation.")
        return

    model = ScreenSenseNet(pretrained=False).to(device)
    ckpt  = torch.load(CKPT, map_location=device)
    model.load_state_dict(ckpt["model_state"])
    model.eval()

    dataset = SaliconDataset(config.VAL_IMG_DIR, config.VAL_MAP_DIR, split="val")
    indices = np.random.choice(len(dataset), n, replace=False)

    n_cols = 4   # original | gt | predicted | overlay
    n_rows = n

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, n * 4))
    headers   = ["Original", "GT Saliency", "Predicted", "Overlay"]
    for c, h in enumerate(headers):
        axes[0, c].set_title(h, fontsize=10, fontweight="bold")

    for row, idx in enumerate(indices):
        raw_img, raw_map = dataset.get_raw_pair(idx)
        tensor, _        = dataset[idx]

        with torch.no_grad():
            if config.USE_AMP:
                with torch.cuda.amp.autocast():
                    pred = model(tensor.unsqueeze(0).to(device))
            else:
                pred = model(tensor.unsqueeze(0).to(device))

        pred_map = _normalise(pred.squeeze().cpu().numpy())
        gt_map   = _normalise(np.array(raw_map, dtype=np.float32) / 255.0)
        img_np   = np.array(raw_img)

        # Overlay
        from utils import overlay_heatmap
        overlay = overlay_heatmap(img_np, pred_map, alpha=0.5)

        axes[row, 0].imshow(img_np)
        axes[row, 1].imshow(gt_map,   cmap="jet", vmin=0, vmax=1)
        axes[row, 2].imshow(pred_map, cmap="jet", vmin=0, vmax=1)
        axes[row, 3].imshow(overlay)

        for ax in axes[row]:
            ax.axis("off")

    plt.tight_layout()
    out = os.path.join(RESULTS, "attention_samples.png")
    plt.savefig(out, dpi=120, bbox_inches="tight"); plt.close()
    print(f"Attention samples → {out}")


if __name__ == "__main__":
    Path(RESULTS).mkdir(parents=True, exist_ok=True)
    plot_curves_from_json()
    attention_samples(n=15)
    print("Done.")
