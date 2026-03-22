"""
ScreenSenseNet model definition — identical to ml/model.py.
Kept here so the backend has no dependency on the ml/ training code.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models


class DecoderBlock(nn.Module):
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


class MobileNetV2Encoder(nn.Module):
    OUT_CHANNELS = [16, 24, 32, 96, 1280]

    def __init__(self):
        super().__init__()
        features    = models.mobilenet_v2(weights=None).features
        self.stage0 = features[0 :2 ]
        self.stage1 = features[2 :4 ]
        self.stage2 = features[4 :7 ]
        self.stage3 = features[7 :14]
        self.stage4 = features[14:19]

    def forward(self, x):
        s0 = self.stage0(x)
        s1 = self.stage1(s0)
        s2 = self.stage2(s1)
        s3 = self.stage3(s2)
        s4 = self.stage4(s3)
        return s0, s1, s2, s3, s4


class ScreenSenseNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = MobileNetV2Encoder()
        enc_ch = MobileNetV2Encoder.OUT_CHANNELS

        self.dec4 = DecoderBlock(enc_ch[4], enc_ch[3], 256)
        self.dec3 = DecoderBlock(256,       enc_ch[2], 128)
        self.dec2 = DecoderBlock(128,       enc_ch[1], 64)
        self.dec1 = DecoderBlock(64,        enc_ch[0], 32)

        self.final_up = nn.Sequential(
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
        if out.shape[2:] != x.shape[2:]:
            out = F.interpolate(out, size=x.shape[2:], mode="bilinear", align_corners=False)
        return self.head(out)
