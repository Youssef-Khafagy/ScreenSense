"""
Loss functions for saliency prediction.

Combined loss = KL_WEIGHT * kl_div + CC_WEIGHT * (1 - cc) + BCE_WEIGHT * bce
"""
import torch
import torch.nn as nn
import torch.nn.functional as F

import config


EPS = 1e-8


# ── Individual losses ─────────────────────────────────────────────────────────

def kl_divergence_loss(pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    """
    KL Divergence treating both maps as probability distributions.

    pred / target: (B, 1, H, W), values in [0, 1]
    Both are normalised to sum to 1 per sample before computing KL.
    """
    pred   = pred.view(pred.size(0), -1)
    target = target.view(target.size(0), -1)

    # Normalise to valid distributions
    pred   = pred   / (pred.sum(dim=1, keepdim=True)   + EPS)
    target = target / (target.sum(dim=1, keepdim=True) + EPS)

    # KL(target || pred)  — standard formulation for saliency
    kl = (target * torch.log(target / (pred + EPS) + EPS)).sum(dim=1)
    return kl.mean()


def correlation_coefficient_loss(pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    """
    Pearson correlation coefficient between predicted and GT maps.
    Returns the *negative* CC so we minimise it (higher CC is better).
    """
    pred   = pred.view(pred.size(0), -1)
    target = target.view(target.size(0), -1)

    pred_m   = pred   - pred.mean(dim=1, keepdim=True)
    target_m = target - target.mean(dim=1, keepdim=True)

    cc = (pred_m * target_m).sum(dim=1) / (
        torch.sqrt((pred_m ** 2).sum(dim=1) * (target_m ** 2).sum(dim=1)) + EPS
    )
    # We want to *maximise* CC, so return 1 - CC as a loss term
    return (1 - cc).mean()


def bce_loss(pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    """
    Pixel-wise Binary Cross-Entropy.  Both pred and target in [0, 1].
    Disabled autocast — F.binary_cross_entropy is unsafe inside AMP context.
    """
    target_norm = target / (target.amax(dim=(1, 2, 3), keepdim=True) + EPS)
    with torch.amp.autocast('cuda', enabled=False):
        return F.binary_cross_entropy(pred.float(), target_norm.clamp(0, 1).float())


# ── Combined loss ─────────────────────────────────────────────────────────────

class SaliencyLoss(nn.Module):
    """
    Weighted combination of KL Divergence, CC loss, and BCE.

        loss = kl_w * KL  +  cc_w * (1 - CC)  +  bce_w * BCE
    """

    def __init__(
        self,
        kl_weight:  float = config.KL_WEIGHT,
        cc_weight:  float = config.CC_WEIGHT,
        bce_weight: float = config.BCE_WEIGHT,
    ):
        super().__init__()
        self.kl_w  = kl_weight
        self.cc_w  = cc_weight
        self.bce_w = bce_weight

    def forward(self, pred: torch.Tensor, target: torch.Tensor):
        kl  = kl_divergence_loss(pred, target)
        cc  = correlation_coefficient_loss(pred, target)
        bce = bce_loss(pred, target)

        total = self.kl_w * kl + self.cc_w * cc + self.bce_w * bce

        return total, {"kl": kl.item(), "cc": cc.item(), "bce": bce.item()}
