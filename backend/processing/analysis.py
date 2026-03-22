"""
Attention region detection and metric computation.
"""
import numpy as np
from scipy import ndimage


EPS = 1e-8

# ── Hotspot detection ─────────────────────────────────────────────────────────

def find_top_hotspots(sal_map: np.ndarray, n: int = 3, min_distance: int = 20) -> list[dict]:
    """
    Find the top N attention hotspots using peak detection with minimum separation.

    Returns a list of dicts:
        { x, y, intensity, label }  (x=col, y=row in image coordinates)
    """
    labels = ["Primary focus", "Secondary focus", "Tertiary focus",
              "4th focus", "5th focus"]

    hotspots  = []
    remaining = sal_map.copy()

    for i in range(n):
        if remaining.max() < EPS:
            break

        # Find the current maximum
        flat_idx = np.argmax(remaining)
        row, col = np.unravel_index(flat_idx, remaining.shape)
        intensity = float(sal_map[row, col])

        hotspots.append({
            "x":         int(col),
            "y":         int(row),
            "intensity": round(intensity, 4),
            "label":     labels[i] if i < len(labels) else f"Focus {i+1}",
        })

        # Suppress a disk around the found peak so next search finds a different region
        Y, X = np.ogrid[:remaining.shape[0], :remaining.shape[1]]
        mask = (X - col) ** 2 + (Y - row) ** 2 <= min_distance ** 2
        remaining[mask] = 0.0

    return hotspots


# ── Attention metrics ─────────────────────────────────────────────────────────

def compute_attention_spread(sal_map: np.ndarray) -> float:
    """
    Entropy-based attention spread.
    Returns a value in [0, 1]: 0 = perfectly focused, 1 = uniformly spread.
    """
    flat = sal_map.flatten().astype(np.float64)
    flat = flat / (flat.sum() + EPS)
    flat = flat[flat > EPS]

    entropy     = float(-np.sum(flat * np.log(flat + EPS)))
    max_entropy = float(np.log(sal_map.size))
    return round(entropy / (max_entropy + EPS), 4)


def top_region_label(sal_map: np.ndarray) -> str:
    """Describe which broad region has the most attention (rule-based)."""
    h, w = sal_map.shape
    regions = {
        "top-left":     sal_map[:h//2,  :w//2].mean(),
        "top-center":   sal_map[:h//2,  w//4:3*w//4].mean(),
        "top-right":    sal_map[:h//2,  w//2:].mean(),
        "center-left":  sal_map[h//4:3*h//4, :w//2].mean(),
        "center":       sal_map[h//4:3*h//4, w//4:3*w//4].mean(),
        "center-right": sal_map[h//4:3*h//4, w//2:].mean(),
        "bottom-left":  sal_map[h//2:, :w//2].mean(),
        "bottom-center":sal_map[h//2:, w//4:3*w//4].mean(),
        "bottom-right": sal_map[h//2:, w//2:].mean(),
    }
    return max(regions, key=regions.get)


# ── 3×3 attention grid ────────────────────────────────────────────────────────

def compute_attention_grid(sal_map: np.ndarray) -> list[list[float]]:
    """
    Divide the saliency map into a 3×3 grid.
    Returns a 3×3 list of floats (percentage of total attention per cell).
    """
    h, w     = sal_map.shape
    total    = sal_map.sum() + EPS
    row_cuts = [0, h // 3, 2 * h // 3, h]
    col_cuts = [0, w // 3, 2 * w // 3, w]

    grid = []
    for r in range(3):
        row = []
        for c in range(3):
            cell = sal_map[row_cuts[r]:row_cuts[r+1], col_cuts[c]:col_cuts[c+1]]
            row.append(round(float(cell.sum() / total * 100), 2))
        grid.append(row)
    return grid


# ── Main ──────────────────────────────────────────────────────────────────────

def analyse_saliency(sal_map: np.ndarray) -> dict:
    """
    Run all attention analyses and return the scores dict for the API response.
    """
    hotspots = find_top_hotspots(sal_map, n=3)

    return {
        "scores": {
            "top_region":       top_region_label(sal_map),
            "attention_spread": compute_attention_spread(sal_map),
            "peak_intensity":   round(float(sal_map.max()), 4),
        },
        "attention_regions":  hotspots,
        "attention_grid":     compute_attention_grid(sal_map),
    }
