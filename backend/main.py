"""
ScreenSense — FastAPI backend.

Endpoints:
  GET  /api/health     → liveness check
  POST /api/predict    → saliency prediction
"""
import io
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image, UnidentifiedImageError

from model.inference import load_model, predict_saliency, is_model_loaded
from processing.heatmap import generate_heatmap_outputs
from processing.analysis import analyse_saliency

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("screensense")

# ── App lifecycle ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Loading saliency model …")
    try:
        load_model()
        log.info("Model ready.")
    except FileNotFoundError as e:
        log.warning(f"Model not found — /api/predict will fail: {e}")
    yield
    log.info("Shutting down.")


app = FastAPI(
    title="ScreenSense API",
    description="AI-powered visual attention prediction",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://*.vercel.app",     # adjust to your Vercel domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Constants ─────────────────────────────────────────────────────────────────

MAX_FILE_SIZE   = 10 * 1024 * 1024   # 10 MB
ALLOWED_TYPES   = {"image/jpeg", "image/png", "image/webp", "image/gif"}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status":       "ok",
        "model_loaded": is_model_loaded(),
    }


@app.post("/api/predict")
async def predict(file: UploadFile = File(...)):
    t0 = time.perf_counter()

    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file.content_type}. "
                   f"Accepted: {', '.join(ALLOWED_TYPES)}",
        )

    # Read and validate size
    raw = await file.read()
    if len(raw) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(raw)/1e6:.1f} MB). Max 10 MB.",
        )

    # Parse image
    try:
        img = Image.open(io.BytesIO(raw)).convert("RGB")
    except (UnidentifiedImageError, Exception) as e:
        raise HTTPException(status_code=422, detail=f"Could not parse image: {e}")

    # Model inference
    try:
        sal_map, img_resized = predict_saliency(img)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            raise HTTPException(
                status_code=507,
                detail="GPU out of memory — try a smaller image.",
            )
        raise HTTPException(status_code=500, detail=str(e))

    # Heatmap generation
    heatmap_outputs = generate_heatmap_outputs(sal_map, img_resized)

    # Attention analysis
    analysis = analyse_saliency(sal_map)

    elapsed = round(time.perf_counter() - t0, 3)
    log.info(f"Processed {file.filename} ({len(raw)/1e3:.0f} KB) in {elapsed}s")

    return JSONResponse({
        **heatmap_outputs,
        **analysis,
        "processing_time_s": elapsed,
        "image_size": {"width": img_resized.width, "height": img_resized.height},
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
