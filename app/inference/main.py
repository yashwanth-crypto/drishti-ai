"""Drishti-AI inference service.

Wraps the four validated model modules behind HTTP so the Spring Boot backend
can call them. Models load once at startup. Internal service -- the Java
backend is the only intended caller.

    uvicorn main:app --port 8000
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

import m1_vision
import m3_maintenance
import m4_forecast

_startup = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    _startup["vision"] = m1_vision.load()
    _startup["maintenance"] = m3_maintenance.load()
    _startup["forecast"] = m4_forecast.load()
    yield


app = FastAPI(title="Drishti-AI Inference", version="1.0.0", lifespan=lifespan)


class MaintenanceRequest(BaseModel):
    features: dict[str, float]


class HistoryPoint(BaseModel):
    week: str
    value: float


class ForecastRequest(BaseModel):
    category: str
    horizon: int = Field(default=4, ge=1, le=52)
    # Omit to forecast from the recorded weekly series on disk.
    history: list[HistoryPoint] | None = None


@app.get("/health")
def health():
    return {"status": "ok", "models": _startup}


@app.post("/predict/vision")
async def predict_vision(image: UploadFile = File(...)):
    try:
        return m1_vision.predict_bytes(await image.read())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read image: {exc}")


@app.get("/predict/maintenance/features")
def maintenance_features():
    return {"feature_cols": m3_maintenance.feature_cols()}


@app.post("/predict/maintenance")
def predict_maintenance(req: MaintenanceRequest):
    try:
        return m3_maintenance.predict(req.features)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/predict/forecast/categories")
def forecast_categories():
    return {"categories": m4_forecast.categories()}


@app.post("/predict/forecast")
def predict_forecast(req: ForecastRequest):
    try:
        if req.history is None:
            history = m4_forecast.recorded_history(req.category)
            source = "recorded"
        else:
            history = [{"week": h.week, "value": h.value} for h in req.history]
            source = "request"
        return {
            "category": req.category,
            "history_source": source,
            "history_weeks": len(history),
            "forecast": m4_forecast.forecast(req.category, history, req.horizon),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
