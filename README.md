# ScreenSense · AI Visual Attention Predictor

> See what your users see before they do.

ScreenSense is a full-stack AI application that predicts visual attention in images.
Upload any screenshot, advertisement, or UI design and get an instant heatmap showing
where human eyes will look first, second, and third, powered by a custom-trained CNN.

---

## How it works

```
Image → Resize + ImageNet normalisation → MobileNetV2 Encoder (5 scales)
      → U-Net Decoder (skip connections) → Saliency Map [0,1]
      → Jet colormap → Heatmap overlay → Attention region analysis → UI
```

1. The uploaded image is resized to 256×192 and ImageNet-normalised
2. The MobileNetV2 encoder extracts features at 5 scales (stride 2→32)
3. The U-Net-style decoder upsamples back to full resolution using skip connections
4. A jet colormap is applied to produce the visual heatmap
5. Top-3 hotspots are detected via peak suppression; entropy-based attention spread and 3×3 region grid are computed
6. Rule-based design tips are generated from the analysis (no LLM)

---

## The Model

### Architecture

**Encoder:** MobileNetV2 pretrained on ImageNet, feature extraction at 5 scales.

**Decoder:** 4 upsampling blocks with skip connections from the encoder (U-Net pattern).
Each block: Upsample → Concat(skip) → Conv → BN → ReLU → Conv → BN → ReLU.

**Output:** Single-channel saliency map in [0, 1], same resolution as input.

**Parameters:** 6,626,481 total

### Training Data

**SALICON dataset:** 10,000 training + 5,000 validation natural images from MS COCO 2014,
annotated with crowd-sourced human fixation maps. Participants indicated where their
attention went on each image via mouse tracking; these are used as ground truth saliency maps.

Images were downloaded from MS COCO 2014. Saliency maps were downloaded from the
SALICON Google Drive distribution via `gdown`.

### Training Details

| Setting                  | Value                             |
|--------------------------|-----------------------------------|
| Backbone                 | MobileNetV2 (ImageNet pretrained) |
| Input size               | 256 × 192                         |
| Batch size               | 8                                 |
| Encoder LR               | 1e-5                              |
| Decoder LR               | 1e-4                              |
| Optimizer                | Adam + weight decay 1e-4          |
| Loss                     | KL Div + CC + BCE (weighted)      |
| Encoder frozen (epochs)  | First 5 epochs                    |
| Early stopping patience  | 5 epochs                          |
| Mixed precision          | Yes (torch.cuda.amp)              |
| GPU                      | NVIDIA GTX 1650 (4 GB VRAM)       |
| Epochs trained           | 13 (early stopping at epoch 13)   |
| Total training time      | ~113 minutes                      |
| Best validation loss     | 0.3256                            |

Early stopping triggered at epoch 13 (validation loss had not improved for 5 consecutive
epochs). Best checkpoint was from epoch 8.

### Evaluation Results

Evaluated on the full SALICON validation set (5,000 images):

| Metric   | Score      | Direction | What it measures                                        |
|----------|------------|-----------|----------------------------------------------------------|
| AUC-Judd | **0.9613** | ↑ higher  | Can the model rank fixated pixels above non-fixated ones? |
| CC       | **0.8756** | ↑ higher  | Pearson correlation between predicted and ground truth heatmap |
| NSS      | **2.163**  | ↑ higher  | Predicted saliency 2.16 std above average at fixation points |
| SIM      | **0.7649** | ↑ higher  | Histogram intersection: 76% overlap with ground truth distribution |
| KL-Div   | **0.2383** | ↓ lower   | Distribution divergence from ground truth (0 = perfect)  |

Published SALICON baseline (typical MobileNet-scale model): AUC ~0.87, CC ~0.74.
This model exceeds the baseline on all 5 metrics.

---

## Tech Stack

| Layer     | Technology                                              |
|-----------|---------------------------------------------------------|
| ML        | Python 3.10 · PyTorch · torchvision · MobileNetV2       |
| Dataset   | SALICON (MS COCO 2014 + crowd-sourced fixation maps)    |
| Backend   | FastAPI · Uvicorn · scipy · Pillow · matplotlib         |
| Frontend  | Next.js 14 (App Router) · TypeScript · Tailwind CSS     |

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- NVIDIA GPU with 4 GB+ VRAM recommended (CPU works, ~2s inference)

### 1. Download the dataset

```bash
cd ml/
pip install -r requirements.txt

# Download MS COCO 2014 images (~20 GB)
python download_data.py --coco-only

# Download SALICON saliency maps via gdown (~431 MB)
pip install gdown
python download_data.py --gdrive

# Verify: should show 10,000 train + 5,000 val maps
python download_data.py --verify
```

### 2. Train the model

```bash
python train.py          # ~2 hours on GTX 1650, early stops when val loss plateaus
python evaluate.py       # compute all 5 metrics on validation set
```

The best model is saved automatically to `ml/checkpoints/best_model.pth` and
copied to `backend/model/best_model.pth`.

### 3. Run the backend

```bash
cd backend/
pip install -r requirements.txt
python main.py           # FastAPI server on http://localhost:8000
```

Test: `curl http://localhost:8000/api/health` → `{"status":"ok","model_loaded":true}`

### 4. Run the frontend

```bash
cd frontend/
npm install
npm run dev              # http://localhost:3000
```

---

## Why this matters

- **UX Design:** Validate that CTAs and key content get the attention they deserve before shipping
- **Advertising:** Predict which elements of an ad will capture attention and optimise accordingly
- **Accessibility:** Ensure important information isn't placed where users naturally ignore
- **A/B testing:** Compare attention maps of two designs without running a live experiment

---

## Future work

- Fine-tune on UI-specific data (web screenshots, app interfaces)
- Larger backbone (EfficientNet, ResNet50) for higher accuracy
- Video saliency support (optical flow + temporal attention)
- Gaze replay animation: show predicted scanpath, not just the static map
- Browser extension for real-time webpage analysis

---

## Project structure

```
screensense/
├── ml/                  # Training pipeline
│   ├── train.py         # Main training loop with AMP, early stopping, checkpointing
│   ├── evaluate.py      # All 5 saliency metrics on validation set
│   ├── model.py         # MobileNetV2 encoder-decoder architecture
│   ├── dataset.py       # PyTorch Dataset for SALICON
│   ├── losses.py        # KL Divergence + CC + BCE combined loss
│   ├── metrics.py       # AUC-Judd, CC, NSS, SIM, KL-Div implementations
│   ├── config.py        # All hyperparameters in one place
│   └── download_data.py # Dataset download script (COCO + SALICON)
├── backend/             # FastAPI inference server
│   ├── main.py          # API endpoints (/api/predict, /api/health)
│   ├── model/           # Model architecture + inference + weights
│   └── processing/      # Heatmap generation, attention analysis
├── frontend/            # Next.js application
│   ├── app/             # Pages (landing, results)
│   └── components/      # UI components (ImageViewer, AttentionPanel, etc.)
└── data/                # Dataset (gitignored, ~20 GB)
```
