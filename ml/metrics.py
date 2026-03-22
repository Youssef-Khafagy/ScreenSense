"""
Standard saliency evaluation metrics.

All functions accept numpy arrays of shape (H, W) with float values.
  pred_map  : predicted saliency map, values in [0, 1]
  gt_map    : ground-truth saliency map (continuous), values in [0, 1]
  fixation  : binary fixation map (1 = fixation point, 0 = not)

References:
  MIT Saliency Benchmark — https://saliency.tuebingen.ai/
"""
import numpy as np
from sklearn.metrics import roc_auc_score

EPS = 1e-8


# ── Helper ────────────────────────────────────────────────────────────────────

def _normalise(x: np.ndarray) -> np.ndarray:
    """Min-max normalise to [0, 1]."""
    mn, mx = x.min(), x.max()
    if mx - mn < EPS:
        return np.zeros_like(x)
    return (x - mn) / (mx - mn + EPS)


def _normalise_sum(x: np.ndarray) -> np.ndarray:
    """Normalise so values sum to 1 (treat as distribution)."""
    s = x.sum()
    if s < EPS:
        return np.zeros_like(x)
    return x / (s + EPS)


# ── AUC-Judd ──────────────────────────────────────────────────────────────────

def auc_judd(pred_map: np.ndarray, fixation_map: np.ndarray) -> float:
    """
    Area Under the ROC Curve (Judd version).
    Uses binary fixation map as labels; predicted saliency as scores.
    """
    fixation_map = (fixation_map > 0.5).astype(int).flatten()
    pred_flat    = pred_map.flatten()

    if fixation_map.sum() == 0:
        return float("nan")

    try:
        return roc_auc_score(fixation_map, pred_flat)
    except Exception:
        return float("nan")


# ── Correlation Coefficient ───────────────────────────────────────────────────

def correlation_coefficient(pred_map: np.ndarray, gt_map: np.ndarray) -> float:
    """Linear Pearson correlation between predicted and GT saliency maps."""
    pred = pred_map.flatten().astype(np.float64)
    gt   = gt_map.flatten().astype(np.float64)

    pred = (pred - pred.mean()) / (pred.std() + EPS)
    gt   = (gt   - gt.mean())   / (gt.std()   + EPS)

    return float(np.corrcoef(pred, gt)[0, 1])


# ── NSS ───────────────────────────────────────────────────────────────────────

def nss(pred_map: np.ndarray, fixation_map: np.ndarray) -> float:
    """
    Normalized Scanpath Saliency.
    Mean normalised saliency at fixated locations.
    """
    pred = pred_map.flatten().astype(np.float64)
    fix  = (fixation_map.flatten() > 0.5)

    if fix.sum() == 0:
        return float("nan")

    pred_norm = (pred - pred.mean()) / (pred.std() + EPS)
    return float(pred_norm[fix].mean())


# ── SIM (Similarity) ──────────────────────────────────────────────────────────

def similarity(pred_map: np.ndarray, gt_map: np.ndarray) -> float:
    """
    Similarity (histogram intersection) between predicted and GT distributions.
    """
    pred = _normalise_sum(pred_map.astype(np.float64).flatten())
    gt   = _normalise_sum(gt_map.astype(np.float64).flatten())
    return float(np.minimum(pred, gt).sum())


# ── KL Divergence ─────────────────────────────────────────────────────────────

def kl_divergence(pred_map: np.ndarray, gt_map: np.ndarray) -> float:
    """
    KL Divergence  KL(GT || Pred).
    Lower is better.
    """
    pred = _normalise_sum(pred_map.astype(np.float64).flatten()) + EPS
    gt   = _normalise_sum(gt_map.astype(np.float64).flatten())   + EPS
    return float((gt * np.log(gt / pred)).sum())


# ── Batch helper ─────────────────────────────────────────────────────────────

def compute_all_metrics(
    pred_map:    np.ndarray,
    gt_map:      np.ndarray,
    fixation_map: np.ndarray,
) -> dict:
    """Compute all 5 metrics for a single image pair."""
    pred_map  = _normalise(pred_map)
    gt_map    = _normalise(gt_map)

    return {
        "AUC-Judd": auc_judd(pred_map, fixation_map),
        "CC":       correlation_coefficient(pred_map, gt_map),
        "NSS":      nss(pred_map, fixation_map),
        "SIM":      similarity(pred_map, gt_map),
        "KL-Div":   kl_divergence(pred_map, gt_map),
    }
