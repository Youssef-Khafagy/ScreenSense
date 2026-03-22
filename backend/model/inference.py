"""
Model loading and inference logic for the FastAPI backend.
"""
import os
import io
import numpy as np
from pathlib import Path

import torch
import torchvision.transforms as T
import torchvision.transforms.functional as TF
from PIL import Image

from huggingface_hub import hf_hub_download
from .network import ScreenSenseNet

# ── Constants ─────────────────────────────────────────────────────────────────

IMAGE_SIZE    = (256, 192)    # (W, H)  — must match training config
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD  = (0.229, 0.224, 0.225)
MODEL_PATH    = Path(__file__).parent / "best_model.pth"
MAX_LONG_SIDE = 1920
HF_REPO_ID    = "Youssef-Khafagy/screensense-saliency"
HF_FILENAME   = "best_model.pth"


def _ensure_model_downloaded():
    if MODEL_PATH.exists():
        return
    print("Model weights not found locally — downloading from HuggingFace Hub...")
    downloaded = hf_hub_download(repo_id=HF_REPO_ID, filename=HF_FILENAME)
    import shutil
    shutil.copy(downloaded, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")


# ── Model singleton ───────────────────────────────────────────────────────────

_model  = None
_device = None


def _get_device() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_model() -> ScreenSenseNet:
    global _model, _device
    if _model is not None:
        return _model

    _device = _get_device()
    _model  = ScreenSenseNet().to(_device)

    _ensure_model_downloaded()

    ckpt = torch.load(str(MODEL_PATH), map_location=_device)
    _model.load_state_dict(ckpt["model_state"])
    _model.eval()
    print(f"Model loaded on {_device}  (from {MODEL_PATH})")
    return _model


def is_model_loaded() -> bool:
    return _model is not None


# ── Preprocessing ─────────────────────────────────────────────────────────────

_normalize = T.Normalize(IMAGENET_MEAN, IMAGENET_STD)


def preprocess_image(img: Image.Image):
    """
    Resize, normalise.
    Returns (tensor, original_resized_pil).
    """
    # Guard against very large uploads
    w, h = img.size
    longest = max(w, h)
    if longest > MAX_LONG_SIDE:
        scale = MAX_LONG_SIDE / longest
        img   = img.resize((int(w * scale), int(h * scale)), Image.BILINEAR)

    img_resized = img.resize(IMAGE_SIZE, Image.BILINEAR)
    tensor      = _normalize(TF.to_tensor(img_resized)).unsqueeze(0)
    return tensor, img_resized


# ── Inference ─────────────────────────────────────────────────────────────────

@torch.no_grad()
def predict_saliency(img: Image.Image) -> tuple[np.ndarray, Image.Image]:
    """
    Run the model on a PIL image.

    Returns:
        sal_map      : (H, W) float32 saliency map in [0, 1], normalised
        img_resized  : PIL image resized to model input dimensions
    """
    model  = load_model()
    tensor, img_resized = preprocess_image(img)

    if torch.cuda.is_available():
        with torch.cuda.amp.autocast():
            out = model(tensor.to(_device))
    else:
        out = model(tensor.to(_device))

    sal_map = out.squeeze().cpu().numpy()   # (H, W)

    # Min-max normalise to [0, 1]
    mn, mx = sal_map.min(), sal_map.max()
    if mx - mn > 1e-8:
        sal_map = (sal_map - mn) / (mx - mn)
    else:
        sal_map = np.zeros_like(sal_map)

    return sal_map, img_resized
