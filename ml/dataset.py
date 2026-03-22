"""
SALICON PyTorch Dataset with preprocessing and augmentation.
"""
import os
import numpy as np
from pathlib import Path
from typing import Tuple, Optional

from PIL import Image
import torch
from torch.utils.data import Dataset
import torchvision.transforms as T
import torchvision.transforms.functional as TF
import random

import config


class SaliconDataset(Dataset):
    """
    Loads image + saliency map pairs from the SALICON directory structure:

        data/
          train/images/*.jpg   data/train/maps/*.png
          val/images/*.jpg     data/val/maps/*.png

    Ground-truth maps can be .png or .jpg; images can be .jpg or .jpeg.
    The map stem must match the image stem (SALICON follows this convention).
    """

    def __init__(
        self,
        img_dir: str,
        map_dir: str,
        split: str = "train",
        image_size: Tuple[int, int] = config.IMAGE_SIZE,
    ):
        self.img_dir    = Path(img_dir)
        self.map_dir    = Path(map_dir)
        self.split      = split
        self.image_size = image_size   # (W, H)

        # Collect paired (image_path, map_path) tuples
        self.pairs = self._collect_pairs()
        if len(self.pairs) == 0:
            raise RuntimeError(
                f"No image/map pairs found in {img_dir} / {map_dir}. "
                "Run ml/download_data.py first."
            )

        # ImageNet normalisation for the encoder backbone
        self.img_normalize = T.Normalize(
            mean=config.IMAGENET_MEAN,
            std=config.IMAGENET_STD,
        )

    # ── Internal helpers ──────────────────────────────────────────────────

    def _collect_pairs(self):
        img_exts = {".jpg", ".jpeg", ".png"}
        map_exts = {".png", ".jpg", ".jpeg"}

        pairs = []
        for img_path in sorted(self.img_dir.iterdir()):
            if img_path.suffix.lower() not in img_exts:
                continue
            stem = img_path.stem
            map_path = None
            for ext in map_exts:
                candidate = self.map_dir / (stem + ext)
                if candidate.exists():
                    map_path = candidate
                    break
            if map_path is not None:
                pairs.append((img_path, map_path))
        return pairs

    # ── Augmentation (training only) ──────────────────────────────────────

    def _augment(self, image: Image.Image, sal_map: Image.Image):
        """Apply identical random transforms to image and map."""
        # Random horizontal flip
        if random.random() > 0.5:
            image   = TF.hflip(image)
            sal_map = TF.hflip(sal_map)

        # Slight colour jitter on image only
        jitter = T.ColorJitter(
            brightness=0.2, contrast=0.2, saturation=0.2, hue=0.05
        )
        image = jitter(image)

        return image, sal_map

    # ── Dataset interface ─────────────────────────────────────────────────

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx: int):
        img_path, map_path = self.pairs[idx]

        # Load
        image   = Image.open(img_path).convert("RGB")
        sal_map = Image.open(map_path).convert("L")   # grayscale

        # Resize  (PIL uses (W, H))
        w, h = self.image_size
        image   = image.resize((w, h), Image.BILINEAR)
        sal_map = sal_map.resize((w, h), Image.BILINEAR)

        # Augment training set
        if self.split == "train":
            image, sal_map = self._augment(image, sal_map)

        # To tensor
        image   = TF.to_tensor(image)                 # [3, H, W], float32 0-1
        sal_map = TF.to_tensor(sal_map)               # [1, H, W], float32 0-1

        # Normalise saliency map to sum to 1 (probability distribution)
        total = sal_map.sum()
        if total > 0:
            sal_map = sal_map / total

        # Normalise image with ImageNet stats
        image = self.img_normalize(image)

        return image, sal_map

    # ── Utility ──────────────────────────────────────────────────────────

    def get_raw_pair(self, idx: int):
        """Return (PIL image, PIL saliency map) without any transforms — for viz."""
        img_path, map_path = self.pairs[idx]
        image   = Image.open(img_path).convert("RGB")
        sal_map = Image.open(map_path).convert("L")
        w, h    = self.image_size
        return (
            image.resize((w, h), Image.BILINEAR),
            sal_map.resize((w, h), Image.BILINEAR),
        )


def get_dataloaders(batch_size: int = config.BATCH_SIZE, num_workers: int = config.NUM_WORKERS):
    """Return (train_loader, val_loader)."""
    train_dataset = SaliconDataset(
        config.TRAIN_IMG_DIR, config.TRAIN_MAP_DIR, split="train"
    )
    val_dataset = SaliconDataset(
        config.VAL_IMG_DIR, config.VAL_MAP_DIR, split="val"
    )

    train_loader = torch.utils.data.DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=True,
    )
    val_loader = torch.utils.data.DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
    )

    print(f"Train: {len(train_dataset)} samples | Val: {len(val_dataset)} samples")
    return train_loader, val_loader
