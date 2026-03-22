# ScreenSense · ML Training Pipeline

End-to-end saliency prediction pipeline trained on the SALICON dataset.
The model takes an RGB image and outputs a single-channel saliency map
predicting where human eyes will look.

---

## Dataset Setup

SALICON uses images from MS COCO 2014 with crowd-sourced fixation maps as ground truth.
The `salicon.net/download` page is no longer active. Use the scripts below instead.

### Step 1: COCO images (~20 GB)

```bash
python download_data.py --coco-only
```

Downloads MS COCO 2014 train (82K images) and val (40K images).
SALICON only uses 10K train + 5K val of these; the rest are ignored at training time.

### Step 2: SALICON saliency maps (~431 MB)

```bash
pip install gdown
python download_data.py --gdrive
```

Downloads `maps.zip` from the SALICON team's Google Drive via `gdown`.
If that fails, try Kaggle: `python download_data.py --kaggle`

### Verify

```bash
python download_data.py --verify
```

Expected output: 10,000 train maps, 5,000 val maps. All checks passed.

---

## Hyperparameters

All hyperparameters live in `config.py`.

| Parameter                 | Value   | Notes                                      |
|---------------------------|---------|--------------------------------------------|
| `IMAGE_SIZE`              | 256×192 | Width × Height                             |
| `BATCH_SIZE`              | 8       | Safe for 4 GB VRAM                         |
| `LEARNING_RATE_ENCODER`   | 1e-5    | Lower LR for pretrained backbone           |
| `LEARNING_RATE_DECODER`   | 1e-4    | Higher LR for freshly-initialised decoder  |
| `EPOCHS`                  | 25      | Max (early stopping usually fires earlier) |
| `FREEZE_ENCODER_EPOCHS`   | 5       | Decoder-only training for first 5 epochs   |
| `EARLY_STOPPING_PATIENCE` | 5       | Stop if val loss doesn't improve for 5     |
| `KL_WEIGHT`               | 1.0     | Primary loss component                     |
| `CC_WEIGHT`               | 0.5     | Correlation coefficient loss weight        |
| `BCE_WEIGHT`              | 0.1     | Binary cross-entropy weight                |
| `USE_AMP`                 | True    | Mixed precision (halves VRAM usage)        |

---

## Architecture

```
Input (B, 3, 192, 256)
│
├── MobileNetV2 Encoder (pretrained ImageNet, frozen for first 5 epochs)
│   ├── Stage 0: stride 2  →  16ch  (96×128)
│   ├── Stage 1: stride 4  →  24ch  (48×64)
│   ├── Stage 2: stride 8  →  32ch  (24×32)
│   ├── Stage 3: stride 16 →  96ch  (12×16)
│   └── Stage 4: stride 32 → 1280ch (6×8)
│
└── U-Net Decoder (skip connections from encoder stages)
    ├── DecBlock(1280+96  → 256)  (12×16)
    ├── DecBlock(256+32   → 128)  (24×32)
    ├── DecBlock(128+24   → 64)   (48×64)
    ├── DecBlock(64+16    → 32)   (96×128)
    ├── Upsample + Conv(32 → 16)  (192×256)
    └── Conv(16 → 1) + Sigmoid
         └── Output: (B, 1, 192, 256)  saliency map in [0, 1]
```

Total parameters: 6,626,481

---

## Training

```bash
pip install -r requirements.txt
python train.py
```

### What actually happened

Trained on an NVIDIA GTX 1650 (4 GB VRAM) with mixed precision (AMP).

- Encoder frozen for epochs 1–5, decoder trained alone
- Encoder unfrozen at epoch 6 with lower LR (1e-5)
- Early stopping triggered at epoch 13 (val loss had not improved for 5 epochs)
- Best checkpoint: epoch 8, val loss 0.3256
- Total training time: ~113 minutes

Training logs to stdout every 50 batches and saves `checkpoints/best_model.pth`
whenever validation loss improves. The best model is automatically copied to
`../backend/model/best_model.pth` at the end.

---

## Evaluation

```bash
python evaluate.py
```

Runs all 5 standard saliency metrics on the full 5,000-image validation set.

### Results

| Metric   | Score      | Direction | What it measures                                             |
|----------|------------|-----------|--------------------------------------------------------------|
| AUC-Judd | **0.9613** | ↑ higher  | ROC AUC: ranks fixated pixels above non-fixated ones         |
| CC       | **0.8756** | ↑ higher  | Pearson correlation between predicted and ground truth map   |
| NSS      | **2.163**  | ↑ higher  | Predicted saliency 2.16 std above average at fixation points |
| SIM      | **0.7649** | ↑ higher  | Histogram intersection: 76% overlap with ground truth        |
| KL-Div   | **0.2383** | ↓ lower   | Distribution divergence from ground truth                    |

Published SALICON baseline (typical MobileNet-scale model): AUC ~0.87, CC ~0.74.
This model exceeds the baseline on all 5 metrics.

---

## Loss Function

```
Loss = 1.0 × KL-Divergence(GT ∥ Pred)
     + 0.5 × (1 − Pearson_CC)
     + 0.1 × BCE(Pred, GT_normalised)
```

KL divergence is the standard primary metric in saliency research. It measures
how well the predicted distribution matches the ground truth. CC captures linear
correlation. BCE provides a pixel-wise anchor to prevent map collapse.

Note: BCE is computed outside the AMP autocast context (`torch.amp.autocast(enabled=False)`)
because `F.binary_cross_entropy` is unsafe under float16 autocast.

---

## Visualisation

```bash
python visualize_results.py   # saves comparison_grid.png + training_curves.png
python inference.py --image path/to/image.jpg   # single image inference
```

---

## Reproducing from scratch

```bash
pip install -r requirements.txt

# 1. Download data
python download_data.py --coco-only
pip install gdown
python download_data.py --gdrive
python download_data.py --verify

# 2. Train
python train.py

# 3. Evaluate
python evaluate.py

# 4. Visualise
python visualize_results.py
```

All outputs go to `ml/results/` and `ml/checkpoints/`.
