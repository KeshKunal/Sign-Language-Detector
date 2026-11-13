"""Local model inference API. Confirmed communication stays in the browser."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from sld.config import ACTIONS, DEFAULT_MODEL_PATH, KEYPOINT_COUNT, SEQUENCE_LENGTH

MODEL_PATH = Path(os.environ.get("MEDISIGN_MODEL", DEFAULT_MODEL_PATH)).expanduser()
app = FastAPI(title="MediSign local inference", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("MEDISIGN_CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
_model: Any = None
_model_error: str | None = None


class PredictionRequest(BaseModel):
    sequence: list[list[float]] = Field(description="30 × 1662 MediaPipe Holistic features")


class PredictionResponse(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)
    scores: dict[str, float]


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "model_available": MODEL_PATH.is_file(),
        "model_loaded": _model is not None,
        "model_error": _model_error,
        "model_path": str(MODEL_PATH),
        "labels": list(ACTIONS),
        "sequence_length": SEQUENCE_LENGTH,
        "features_per_frame": KEYPOINT_COUNT,
        "threshold": float(os.environ.get("MEDISIGN_CONFIDENCE_THRESHOLD", "0.65")),
    }


@app.post("/api/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> PredictionResponse:
    global _model, _model_error
    if not MODEL_PATH.is_file():
        raise HTTPException(status_code=503, detail="Model weights are unavailable. Train the model first.")
    try:
        array = np.asarray(request.sequence, dtype=np.float32)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="Sequence must contain numeric landmark values.") from exc
    if array.shape != (SEQUENCE_LENGTH, KEYPOINT_COUNT):
        raise HTTPException(status_code=422, detail=f"Expected ({SEQUENCE_LENGTH}, {KEYPOINT_COUNT}), got {array.shape}.")
    if not np.isfinite(array).all():
        raise HTTPException(status_code=422, detail="Sequence contains non-finite values.")
    try:
        if _model is None:
            from tensorflow.keras.models import load_model
            _model = load_model(MODEL_PATH)
        probabilities = np.asarray(_model.predict(array[None, ...], verbose=0)[0], dtype=float)
        if probabilities.shape != (len(ACTIONS),) or not np.isfinite(probabilities).all():
            raise ValueError("Model output does not match the configured class mapping.")
        index = int(probabilities.argmax())
        return PredictionResponse(
            label=ACTIONS[index],
            confidence=float(probabilities[index]),
            scores={label: float(score) for label, score in zip(ACTIONS, probabilities)},
        )
    except Exception as exc:
        _model_error = str(exc)
        raise HTTPException(status_code=500, detail=f"Model inference failed: {exc}") from exc
