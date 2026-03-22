"""
ScreenSense — All training hyperparameters in one place.
Adjust these to experiment without touching training code.
"""
import os

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR       = os.path.join(ROOT_DIR, "data")
TRAIN_IMG_DIR  = os.path.join(DATA_DIR, "train", "images")
TRAIN_MAP_DIR  = os.path.join(DATA_DIR, "train", "maps")
VAL_IMG_DIR    = os.path.join(DATA_DIR, "val", "images")
VAL_MAP_DIR    = os.path.join(DATA_DIR, "val", "maps")
CHECKPOINT_DIR = os.path.join(ROOT_DIR, "ml", "checkpoints")
RESULTS_DIR    = os.path.join(ROOT_DIR, "ml", "results")

# ── Image / preprocessing ──────────────────────────────────────────────────
IMAGE_SIZE = (256, 192)          # (width, height) — or try (320, 240)
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD  = (0.229, 0.224, 0.225)

# ── Model ──────────────────────────────────────────────────────────────────
ENCODER_BACKBONE      = "mobilenetv2"
FREEZE_ENCODER_EPOCHS = 5        # Freeze backbone for first N epochs

# ── Training ──────────────────────────────────────────────────────────────
BATCH_SIZE              = 8      # Fits comfortably in 4 GB VRAM
NUM_WORKERS             = 4
EPOCHS                  = 25
LEARNING_RATE_ENCODER   = 1e-5   # Lower LR for pretrained backbone
LEARNING_RATE_DECODER   = 1e-4
WEIGHT_DECAY            = 1e-4
EARLY_STOPPING_PATIENCE = 5
LR_PATIENCE             = 3      # Epochs before ReduceLROnPlateau fires
LR_FACTOR               = 0.5
USE_AMP                 = True   # Automatic mixed precision (free speedup)

# ── Loss weights ──────────────────────────────────────────────────────────
KL_WEIGHT  = 1.0
CC_WEIGHT  = 0.5
BCE_WEIGHT = 0.1

# ── Logging ───────────────────────────────────────────────────────────────
LOG_EVERY_N_BATCHES = 50
SAVE_BEST_ONLY      = True

# ── Reproducibility ──────────────────────────────────────────────────────
SEED = 42
