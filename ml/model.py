"""
ScreenSenseNet — MobileNetV2 encoder-decoder with skip connections for saliency prediction.

Architecture:
  Encoder  : MobileNetV2 pretrained on ImageNet (feature extraction at 5 scales)
  Decoder  : 5 upsampling blocks, each with a skip connection from the encoder
  Output   : Single-channel saliency map, same resolution as input, values in [0, 1]
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
from typing import List


# ── Decoder block ─────────────────────────────────────────────────────────────

class DecoderBlock(nn.Module):
    """
    Upsample → concat skip → Conv → BN → ReLU → Conv → BN → ReLU
    """

    def __init__(self, in_channels: int, skip_channels: int, out_channels: int):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels + skip_channels, out_channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        x = F.interpolate(x, size=skip.shape[2:], mode="bilinear", align_corners=False)
        x = torch.cat([x, skip], dim=1)
        return self.conv(x)


# ── Encoder wrapper ───────────────────────────────────────────────────────────

class MobileNetV2Encoder(nn.Module):
    """
    Extracts feature maps at 5 progressively deeper scales from MobileNetV2.

    Output channels at each scale:
      scale0 (stride 2)  : 16  ch
      scale1 (stride 4)  : 24  ch
      scale2 (stride 8)  : 32  ch
      scale3 (stride 16) : 96  ch
      scale4 (stride 32) : 1280 ch  (bottleneck features)
    """

    # MobileNetV2 feature indices for each stride level
    _SCALE_INDICES = [
        (0,  2),   # stride 2  → 16 ch
        (2,  4),   # stride 4  → 24 ch
        (4,  7),   # stride 8  → 32 ch
        (7,  14),  # stride 16 → 96 ch
        (14, 19),  # stride 32 → 1280 ch
    ]
    OUT_CHANNELS = [16, 24, 32, 96, 1280]

    def __init__(self, pretrained: bool = True):
        super().__init__()
        backbone = models.mobilenet_v2(weights="IMAGENET1K_V1" if pretrained else None)
        features = backbone.features   # Sequential of 19 blocks

        self.stage0 = features[0 :2 ]
        self.stage1 = features[2 :4 ]
        self.stage2 = features[4 :7 ]
        self.stage3 = features[7 :14]
        self.stage4 = features[14:19]

    def forward(self, x: torch.Tensor):
        s0 = self.stage0(x)
        s1 = self.stage1(s0)
        s2 = self.stage2(s1)
        s3 = self.stage3(s2)
        s4 = self.stage4(s3)
        return s0, s1, s2, s3, s4   # low-level → high-level

    def freeze(self):
        for p in self.parameters():
            p.requires_grad = False

    def unfreeze(self):
        for p in self.parameters():
            p.requires_grad = True


# ── Full model ────────────────────────────────────────────────────────────────

class ScreenSenseNet(nn.Module):
    """
    Full encoder-decoder saliency prediction network.

    Input  : (B, 3, H, W)  — ImageNet-normalised RGB
    Output : (B, 1, H, W)  — saliency probability map in [0, 1]
    """

    def __init__(self, pretrained: bool = True):
        super().__init__()
        self.encoder = MobileNetV2Encoder(pretrained=pretrained)

        enc_ch = MobileNetV2Encoder.OUT_CHANNELS   # [16, 24, 32, 96, 1280]

        # Decoder — bottom to top (deepest → shallowest)
        self.dec4 = DecoderBlock(enc_ch[4], enc_ch[3], 256)   # 1280+96  → 256
        self.dec3 = DecoderBlock(256,       enc_ch[2], 128)   # 256+32   → 128
        self.dec2 = DecoderBlock(128,       enc_ch[1], 64)    # 128+24   → 64
        self.dec1 = DecoderBlock(64,        enc_ch[0], 32)    # 64+16    → 32

        # Final upsampling to input resolution
        self.final_up  = nn.Sequential(
            nn.Upsample(scale_factor=2, mode="bilinear", align_corners=False),
            nn.Conv2d(32, 16, 3, padding=1, bias=False),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
        )
        self.head = nn.Sequential(
            nn.Conv2d(16, 1, kernel_size=1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        s0, s1, s2, s3, s4 = self.encoder(x)

        d4 = self.dec4(s4, s3)
        d3 = self.dec3(d4, s2)
        d2 = self.dec2(d3, s1)
        d1 = self.dec1(d2, s0)

        out = self.final_up(d1)

        # Ensure exact spatial match with input
        if out.shape[2:] != x.shape[2:]:
            out = F.interpolate(out, size=x.shape[2:], mode="bilinear", align_corners=False)

        return self.head(out)

    # ── Convenience helpers ──────────────────────────────────────────────

    def freeze_encoder(self):
        self.encoder.freeze()
        print("Encoder frozen.")

    def unfreeze_encoder(self):
        self.encoder.unfreeze()
        print("Encoder unfrozen for fine-tuning.")

    def count_params(self):
        total     = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        print(f"Parameters — total: {total:,}  |  trainable: {trainable:,}")
        return total, trainable


# ── Quick sanity check ────────────────────────────────────────────────────────

if __name__ == "__main__":
    model = ScreenSenseNet(pretrained=False)
    model.eval()
    x = torch.randn(2, 3, 192, 256)
    with torch.no_grad():
        out = model(x)
    print(f"Input:  {x.shape}")
    print(f"Output: {out.shape}")   # Expect (2, 1, 192, 256)
    model.count_params()
