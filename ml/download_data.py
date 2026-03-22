"""
ScreenSense — SALICON Dataset Download Script
=============================================

SALICON uses images from MS COCO 2014.

Automatic download fetches:
  - MS COCO 2014 train images  (~13 GB)  → data/train/images/
  - MS COCO 2014 val images    (~6 GB)   → data/val/images/
  - SALICON saliency maps                → data/train/maps/ + data/val/maps/

salicon.net/download is no longer available. Use one of these instead:

  Option A — Google Drive via gdown (easiest, ~431 MB):
    pip install gdown
    python download_data.py --gdrive

  Option B — Kaggle (~4.3 GB, includes images):
    pip install kaggle
    # Set up ~/.kaggle/kaggle.json (API token from kaggle.com/settings)
    python download_data.py --kaggle

  Option C — Manual: place SALICON_train_maps.zip and SALICON_val_maps.zip
    in data/raw/, then run:  python download_data.py --maps-only

Usage:
    cd ml/
    python download_data.py [--coco-only] [--maps-only] [--gdrive] [--kaggle] [--verify]
"""
import os
import sys
import json
import hashlib
import zipfile
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

# ── Paths ─────────────────────────────────────────────────────────────────────

ROOT_DIR  = Path(__file__).resolve().parent.parent
DATA_DIR  = ROOT_DIR / "data"
RAW_DIR   = DATA_DIR / "raw"

TRAIN_IMG = DATA_DIR / "train" / "images"
TRAIN_MAP = DATA_DIR / "train" / "maps"
VAL_IMG   = DATA_DIR / "val"   / "images"
VAL_MAP   = DATA_DIR / "val"   / "maps"

for d in [DATA_DIR, RAW_DIR, TRAIN_IMG, TRAIN_MAP, VAL_IMG, VAL_MAP]:
    d.mkdir(parents=True, exist_ok=True)


# ── MS COCO 2014 URLs ─────────────────────────────────────────────────────────

COCO_URLS = {
    "train_images": {
        "url":      "http://images.cocodataset.org/zips/train2014.zip",
        "filename": "train2014.zip",
        "size_gb":  13.5,
    },
    "val_images": {
        "url":      "http://images.cocodataset.org/zips/val2014.zip",
        "filename": "val2014.zip",
        "size_gb":  6.3,
    },
}

# SALICON saliency maps — manual download ZIP names
# (used by --maps-only; adjust to whatever filename you downloaded)
SALICON_MAP_ZIPS = {
    "train_maps": "SALICON_train_maps.zip",
    "val_maps":   "SALICON_val_maps.zip",
}

# Google Drive file IDs for SALICON maps (LSUN'17 release, ~431 MB combined)
# Source: alexanderkroner/saliency repo + salicon.net/challenge page
GDRIVE_MAP_IDS = {
    "maps.zip": "1PnO7szbdub1559LfjYHMy65EDC4VhJC8",
}

# Kaggle dataset slug
KAGGLE_DATASET = "roshan401/salicon"

# EXPECTED FILE COUNTS (SALICON subset of COCO 2014)
EXPECTED_COUNTS = {
    "train_images": 10000,
    "val_images":   5000,
    "train_maps":   10000,
    "val_maps":     5000,
}


# ── Download helpers ──────────────────────────────────────────────────────────

class ProgressBar:
    def __init__(self, total_bytes: int, filename: str):
        self.total    = total_bytes
        self.filename = filename
        self.seen     = 0

    def __call__(self, block_count, block_size, total_size):
        if total_size > 0:
            self.total = total_size
        self.seen += block_size
        pct = min(self.seen / self.total * 100, 100)
        gb  = self.seen  / 1e9
        tot = self.total / 1e9
        bar_len = 40
        filled  = int(bar_len * pct / 100)
        bar     = "█" * filled + "░" * (bar_len - filled)
        print(f"\r  {self.filename[:30]:<30} [{bar}] {pct:5.1f}% ({gb:.2f}/{tot:.2f} GB)",
              end="", flush=True)

    def finish(self):
        print()


def download_file(url: str, dest: Path, size_gb: float = 0):
    if dest.exists():
        print(f"  ✓ Already exists: {dest.name}  (skipping)")
        return

    print(f"\n  Downloading {dest.name}  (~{size_gb:.1f} GB) …")
    print(f"  URL: {url}")

    progress = ProgressBar(int(size_gb * 1e9), dest.name)
    try:
        urllib.request.urlretrieve(url, str(dest), reporthook=progress)
        progress.finish()
        print(f"  ✓ Saved to {dest}")
    except urllib.error.URLError as e:
        progress.finish()
        print(f"  ✗ Download failed: {e}")
        raise


def extract_zip(zip_path: Path, dest_dir: Path, desc: str = ""):
    print(f"\n  Extracting {zip_path.name} → {dest_dir}  {desc}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        members = zf.namelist()
        for i, member in enumerate(members):
            zf.extract(member, dest_dir)
            if (i + 1) % 1000 == 0 or i + 1 == len(members):
                pct = (i + 1) / len(members) * 100
                print(f"\r    {pct:5.1f}%  ({i+1}/{len(members)} files)",
                      end="", flush=True)
    print(f"\n  ✓ Extracted {len(members)} files")


# ── COCO download ─────────────────────────────────────────────────────────────

def download_coco_images():
    print("\n" + "=" * 60)
    print("  Downloading MS COCO 2014 images")
    print("=" * 60)

    for split, info in COCO_URLS.items():
        zip_path = RAW_DIR / info["filename"]
        try:
            download_file(info["url"], zip_path, info["size_gb"])
        except Exception:
            print(f"\n  MANUAL DOWNLOAD REQUIRED:")
            print(f"  wget -P data/raw/ {info['url']}")
            continue

        # Extract to data/{train,val}/images/
        split_name = "train" if "train" in split else "val"
        dest_dir   = DATA_DIR / split_name / "images"
        temp_dir   = RAW_DIR / f"coco_{split_name}"

        if not temp_dir.exists():
            extract_zip(zip_path, temp_dir, "(this may take a while)")

        # COCO extracts to train2014/ or val2014/ — move the JPEGs flat
        coco_folder = temp_dir / f"{split_name}2014"
        if coco_folder.exists():
            import shutil
            jpegs = list(coco_folder.glob("*.jpg"))
            print(f"  Moving {len(jpegs)} images → {dest_dir}")
            for i, src in enumerate(jpegs):
                shutil.move(str(src), str(dest_dir / src.name))
                if (i + 1) % 1000 == 0:
                    print(f"\r    {i+1}/{len(jpegs)}", end="", flush=True)
            print()
            coco_folder.rmdir()


# ── SALICON maps extraction ────────────────────────────────────────────────────

def extract_salicon_maps():
    """
    Extract SALICON saliency map ZIPs that the user placed in data/raw/.
    SALICON provides .png saliency maps with the same stem as COCO images.
    """
    print("\n" + "=" * 60)
    print("  Extracting SALICON saliency maps")
    print("=" * 60)

    found_any = False
    for key, zip_name in SALICON_MAP_ZIPS.items():
        zip_path = RAW_DIR / zip_name
        if not zip_path.exists():
            print(f"\n  ✗ Not found: {zip_path}")
            print(f"    Download from http://salicon.net and place in data/raw/")
            continue

        found_any = True
        split     = "train" if "train" in key else "val"
        dest_dir  = DATA_DIR / split / "maps"
        extract_zip(zip_path, dest_dir, f"→ {split} maps")

        # SALICON sometimes nests files inside a subdirectory — flatten
        _flatten_maps(dest_dir)

    if not found_any:
        print_salicon_instructions()


def _flatten_maps(maps_dir: Path):
    """Move any .png files from subdirectories up to maps_dir."""
    for child in list(maps_dir.iterdir()):
        if child.is_dir():
            for png in child.glob("*.png"):
                png.rename(maps_dir / png.name)
            try:
                child.rmdir()
            except OSError:
                pass   # not empty, that's fine


# ── Google Drive download (gdown) ─────────────────────────────────────────────

def download_gdrive():
    """Download SALICON saliency maps from Google Drive using gdown."""
    print("\n" + "=" * 60)
    print("  Downloading SALICON maps via Google Drive (gdown)")
    print("=" * 60)

    try:
        import gdown
    except ImportError:
        print("  ✗ gdown not installed. Run:  pip install gdown")
        return False

    maps_zip = RAW_DIR / "maps.zip"
    if not maps_zip.exists():
        file_id = GDRIVE_MAP_IDS["maps.zip"]
        url = f"https://drive.google.com/uc?id={file_id}"
        print(f"\n  Downloading maps.zip (~431 MB) from Google Drive …")
        try:
            gdown.download(url, str(maps_zip), quiet=False)
        except Exception as e:
            print(f"  ✗ gdown failed: {e}")
            print("  The file may require a signed-in Google account.")
            print("  Try:  gdown --fuzzy 'https://drive.google.com/file/d/"
                  f"{file_id}/view'")
            print("  Or use --kaggle instead.")
            return False
    else:
        print(f"  ✓ Already exists: maps.zip  (skipping download)")

    # Extract — the zip contains train/ and val/ subdirectories
    print(f"\n  Extracting maps.zip …")
    extract_zip(maps_zip, RAW_DIR / "salicon_maps")
    _copy_maps_from_gdrive_extract(RAW_DIR / "salicon_maps")
    return True


def _copy_maps_from_gdrive_extract(extract_dir: Path):
    """
    The SALICON maps.zip from Google Drive unpacks to:
      maps/train/COCO_train2014_*.png
      maps/val/COCO_val2014_*.png
    OR possibly just:
      train/COCO_train2014_*.png
      val/COCO_val2014_*.png
    This function finds the PNGs and copies them to the right places.
    """
    import shutil

    for split, dest in [("train", TRAIN_MAP), ("val", VAL_MAP)]:
        # Try a few common nested structures
        candidates = [
            extract_dir / "maps" / split,
            extract_dir / split,
            extract_dir,
        ]
        png_files = []
        for candidate in candidates:
            if candidate.exists():
                png_files = [p for p in candidate.rglob("*.png")
                             if split in p.name.lower() or split in str(p)]
                if png_files:
                    break

        if not png_files:
            # Fallback: grab ALL pngs from the extract dir for this split
            png_files = [p for p in extract_dir.rglob("*.png")
                         if f"_{split}2014_" in p.name]

        if not png_files:
            print(f"  ✗ Could not find {split} maps in extracted archive.")
            print(f"    Extracted to: {extract_dir}")
            print(f"    Contents: {list(extract_dir.rglob('*'))[:20]}")
            continue

        print(f"  Copying {len(png_files)} {split} maps → {dest}")
        for i, src in enumerate(png_files):
            shutil.copy2(str(src), str(dest / src.name))
            if (i + 1) % 1000 == 0 or (i + 1) == len(png_files):
                print(f"\r    {i+1}/{len(png_files)}", end="", flush=True)
        print()
    print("  ✓ Maps copied.")


# ── Kaggle download ────────────────────────────────────────────────────────────

def download_kaggle():
    """Download SALICON dataset from Kaggle (roshan401/salicon)."""
    print("\n" + "=" * 60)
    print("  Downloading SALICON from Kaggle")
    print("=" * 60)

    try:
        import kaggle  # noqa: F401
    except ImportError:
        print("  ✗ kaggle not installed. Run:  pip install kaggle")
        print("  Also set up ~/.kaggle/kaggle.json  (from kaggle.com/settings → API)")
        return False

    import subprocess, shutil

    kaggle_zip = RAW_DIR / "salicon.zip"
    if not kaggle_zip.exists():
        print(f"\n  Downloading roshan401/salicon (~4.3 GB) from Kaggle …")
        result = subprocess.run(
            ["kaggle", "datasets", "download", KAGGLE_DATASET,
             "-p", str(RAW_DIR), "--unzip"],
            capture_output=False
        )
        if result.returncode != 0:
            print("  ✗ Kaggle download failed.")
            print("  Make sure ~/.kaggle/kaggle.json exists and is valid.")
            return False
    else:
        print(f"  ✓ Already exists: salicon.zip  (skipping download)")

    # The Kaggle dataset structure varies — find and move the maps
    kaggle_extract = RAW_DIR / "salicon_kaggle"
    print(f"\n  Locating maps in Kaggle download …")

    # The maps might already be extracted (--unzip was used), or in a zip
    # Try to find train/val map PNGs anywhere under RAW_DIR
    for split, dest in [("train", TRAIN_MAP), ("val", VAL_MAP)]:
        pattern = f"*{split}*/*.png"
        pngs = list(RAW_DIR.glob(f"**/*{split}2014*.png"))
        if not pngs:
            pngs = list(RAW_DIR.glob(f"**/{split}/**/*.png"))

        if pngs:
            print(f"  Found {len(pngs)} {split} PNGs")
            for i, src in enumerate(pngs):
                shutil.copy2(str(src), str(dest / src.name))
                if (i + 1) % 1000 == 0 or (i + 1) == len(pngs):
                    print(f"\r    {i+1}/{len(pngs)}", end="", flush=True)
            print()
        else:
            print(f"  ✗ Could not auto-locate {split} maps.")
            print(f"    Browse {RAW_DIR} and manually copy PNGs to {dest}")

    return True


# ── Verification ──────────────────────────────────────────────────────────────

def verify():
    print("\n" + "=" * 60)
    print("  Verifying dataset")
    print("=" * 60)

    checks = [
        (TRAIN_IMG, EXPECTED_COUNTS["train_images"], "train images"),
        (VAL_IMG,   EXPECTED_COUNTS["val_images"],   "val images"),
        (TRAIN_MAP, EXPECTED_COUNTS["train_maps"],   "train saliency maps"),
        (VAL_MAP,   EXPECTED_COUNTS["val_maps"],     "val saliency maps"),
    ]

    all_ok = True
    for directory, expected, label in checks:
        actual = len(list(directory.glob("*.*")))
        status = "✓" if actual >= expected * 0.95 else "✗"
        flag   = "" if actual >= expected * 0.95 else "  ← ISSUE"
        print(f"  {status} {label:<30} {actual:>6} / {expected}{flag}")
        if actual < expected * 0.95:
            all_ok = False

    print()
    if all_ok:
        print("  All checks passed. Ready to train.")
    else:
        print("  Some files are missing. Check the notes above.")

    return all_ok


# ── Manual instructions ───────────────────────────────────────────────────────

def print_salicon_instructions():
    print("""
  ┌─────────────────────────────────────────────────────────┐
  │           SALICON MAPS — HOW TO GET THEM                │
  ├─────────────────────────────────────────────────────────┤
  │  salicon.net/download is dead. Use one of these:        │
  │                                                         │
  │  OPTION A — Google Drive via gdown (~431 MB, fastest):  │
  │    pip install gdown                                    │
  │    python download_data.py --gdrive                     │
  │                                                         │
  │  OPTION B — Kaggle (~4.3 GB):                           │
  │    pip install kaggle                                   │
  │    # Create ~/.kaggle/kaggle.json from:                 │
  │    #   kaggle.com → Settings → API → Create New Token   │
  │    python download_data.py --kaggle                     │
  │                                                         │
  │  OPTION C — Manual ZIP placement:                       │
  │    Download SALICON_train_maps.zip and                  │
  │    SALICON_val_maps.zip, place in data/raw/, then:      │
  │    python download_data.py --maps-only                  │
  └─────────────────────────────────────────────────────────┘
""")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Download and prepare SALICON dataset")
    parser.add_argument("--coco-only",  action="store_true", help="Download only COCO images")
    parser.add_argument("--maps-only",  action="store_true", help="Extract SALICON maps from ZIPs in data/raw/")
    parser.add_argument("--gdrive",     action="store_true", help="Download SALICON maps via gdown (Google Drive)")
    parser.add_argument("--kaggle",     action="store_true", help="Download SALICON maps via Kaggle CLI")
    parser.add_argument("--verify",     action="store_true", help="Verify file counts")
    args = parser.parse_args()

    print("\nScreenSense — Dataset Setup")
    print("=" * 60)
    print(f"Data directory: {DATA_DIR}")

    if args.verify:
        verify()
        return

    if args.maps_only:
        extract_salicon_maps()
        verify()
        return

    if args.gdrive:
        ok = download_gdrive()
        if not ok:
            print_salicon_instructions()
        verify()
        return

    if args.kaggle:
        ok = download_kaggle()
        if not ok:
            print_salicon_instructions()
        verify()
        return

    if args.coco_only:
        download_coco_images()
        verify()
        return

    # Default: show instructions
    print_salicon_instructions()


if __name__ == "__main__":
    main()
