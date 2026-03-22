"""
ScreenSense — Single-image inference.

Usage:
    python inference.py --image path/to/image.jpg [--output out.png]

Outputs:
    - out_saliency.png  : coloured heatmap
    - out_overlay.png   : original image with heatmap blended over it
"""
import argparse
import os
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image
import torchvision.transforms.functional as TF
import torchvision.transforms as T
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config
from model import ScreenSenseNet
from utils import get_device, apply_colormap, overlay_heatmap, tensor_to_numpy_image


BEST_CKPT = os.path.join(config.CHECKPOINT_DIR, "best_model.pth")


def load_model(ckpt_path: str, device) -> ScreenSenseNet:
    model = ScreenSenseNet(pretrained=False).to(device)
    ckpt  = torch.load(ckpt_path, map_location=device)
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    return model


def preprocess(img_path: str):
    """Load, resize, normalise.  Returns (tensor, original PIL image)."""
    img = Image.open(img_path).convert("RGB")
    w, h = config.IMAGE_SIZE
    img_resized = img.resize((w, h), Image.BILINEAR)
    tensor = TF.to_tensor(img_resized)
    tensor = T.Normalize(config.IMAGENET_MEAN, config.IMAGENET_STD)(tensor)
    return tensor.unsqueeze(0), img_resized   # (1, 3, H, W)


@torch.no_grad()
def predict(model, tensor: torch.Tensor, device) -> np.ndarray:
    """Return (H, W) numpy saliency map in [0, 1]."""
    out = model(tensor.to(device))
    sal = out.squeeze().cpu().numpy()
    # Min-max normalise
    sal = (sal - sal.min()) / (sal.max() - sal.min() + 1e-8)
    return sal


def run(image_path: str, output_stem: str = None):
    device = get_device()

    if not os.path.exists(BEST_CKPT):
        print(f"ERROR: No checkpoint at {BEST_CKPT}. Run train.py first.")
        sys.exit(1)

    model  = load_model(BEST_CKPT, device)
    tensor, img_pil = preprocess(image_path)
    sal_map         = predict(model, tensor, device)
    img_np          = np.array(img_pil)

    stem = output_stem or Path(image_path).stem
    out_dir = Path(image_path).parent

    # Coloured heatmap
    heatmap = apply_colormap(sal_map, cmap="jet")
    Image.fromarray(heatmap).save(str(out_dir / f"{stem}_saliency.png"))

    # Overlay
    blended = overlay_heatmap(img_np, sal_map, alpha=0.5)
    Image.fromarray(blended).save(str(out_dir / f"{stem}_overlay.png"))

    print(f"Saved → {stem}_saliency.png")
    print(f"Saved → {stem}_overlay.png")

    return sal_map


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ScreenSense single-image inference")
    parser.add_argument("--image",  required=True, help="Path to input image")
    parser.add_argument("--output", default=None,  help="Output filename stem (optional)")
    args = parser.parse_args()
    run(args.image, args.output)
