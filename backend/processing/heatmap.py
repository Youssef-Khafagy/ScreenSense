"""
Heatmap colourisation and overlay generation.
"""
import io
import base64
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ── Core helpers ──────────────────────────────────────────────────────────────

def apply_colormap(sal_map: np.ndarray, cmap: str = "jet") -> np.ndarray:
    """(H, W) float [0,1] → (H, W, 3) uint8 RGB coloured heatmap."""
    cm = plt.get_cmap(cmap)
    return (cm(sal_map)[:, :, :3] * 255).astype(np.uint8)


def overlay_heatmap(
    image_rgb: np.ndarray,
    sal_map:   np.ndarray,
    alpha:     float = 0.45,
    cmap:      str   = "jet",
) -> np.ndarray:
    """Blend heatmap over original image. Returns (H, W, 3) uint8."""
    colored = apply_colormap(sal_map, cmap).astype(np.float32)
    base    = image_rgb.astype(np.float32)
    return np.clip((1 - alpha) * base + alpha * colored, 0, 255).astype(np.uint8)


# ── PIL / base64 helpers ──────────────────────────────────────────────────────

def numpy_to_pil(arr: np.ndarray) -> Image.Image:
    """(H, W, 3) uint8 → PIL Image."""
    return Image.fromarray(arr.astype(np.uint8))


def pil_to_base64(img: Image.Image, fmt: str = "PNG") -> str:
    """PIL Image → base64 data-URI string."""
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def numpy_to_base64(arr: np.ndarray, fmt: str = "PNG") -> str:
    return pil_to_base64(numpy_to_pil(arr), fmt)


# ── Main export function ──────────────────────────────────────────────────────

def generate_heatmap_outputs(
    sal_map:    np.ndarray,
    image_pil:  Image.Image,
    alpha:      float = 0.45,
) -> dict:
    """
    Given a (H, W) saliency map and the resized source image, produce
    three base64-encoded outputs ready for the API response.

    Returns:
        heatmap_base64  : coloured heatmap (jet colormap)
        overlay_base64  : original image with heatmap blended
        raw_map_base64  : grayscale saliency map
    """
    image_np = np.array(image_pil.convert("RGB"))

    # Ensure saliency map matches image dimensions
    if sal_map.shape != (image_np.shape[0], image_np.shape[1]):
        from PIL import Image as PILImage
        sal_pil  = PILImage.fromarray((sal_map * 255).astype(np.uint8), mode="L")
        sal_pil  = sal_pil.resize((image_np.shape[1], image_np.shape[0]), PILImage.BILINEAR)
        sal_map  = np.array(sal_pil, dtype=np.float32) / 255.0

    heatmap_np  = apply_colormap(sal_map)
    overlay_np  = overlay_heatmap(image_np, sal_map, alpha)
    raw_gray_np = (sal_map * 255).astype(np.uint8)

    return {
        "heatmap_base64": numpy_to_base64(heatmap_np),
        "overlay_base64": numpy_to_base64(overlay_np),
        "raw_map_base64": pil_to_base64(Image.fromarray(raw_gray_np, mode="L")),
    }
