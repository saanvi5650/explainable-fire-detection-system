from contextlib import asynccontextmanager
import time
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import DASHBOARD_DIR, SEQUENCE_LENGTH
from .schemas import SensorReading
from .database import init_db, save_event, latest, history, nodes, metrics
from .window_manager import windows
from .risk_engine import baseline_prediction, apply_adaptive_logic, normalise_contributions
from .explanation import build_explanation
from .ml_service import ml_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Explainable Adaptive Fire Detection API",
    version="1.0.0",
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "database": "connected",
        "model_loaded": ml_service.ready,
        "model_error": ml_service.load_error,
        "sequence_length": SEQUENCE_LENGTH
    }

@app.post("/api/readings")
def ingest(reading: SensorReading):
    started = time.perf_counter()
    window = windows.add(reading)

    raw_tier, score, probabilities, baseline_values = baseline_prediction(reading, window)
    source = "baseline"
    explanation_method = "interpretable weighted evidence"
    confidence = probabilities[raw_tier]

    model_result = ml_service.predict(window)
    shap_values = None
    if model_result:
        raw_tier = model_result["tier"]
        confidence = model_result["confidence"]
        probabilities = model_result["probabilities"]
        source = "lstm"
        shap_values = ml_service.shap_contributions(
            model_result["scaled_window"], model_result["class_index"]
        )

    adjusted, confidence, occupied, adaptive_reason = apply_adaptive_logic(
        raw_tier, confidence, reading
    )
    if shap_values:
        contributors = normalise_contributions(shap_values)
        explanation_method = "SHAP GradientExplainer"
    else:
        contributors = normalise_contributions(baseline_values)

    explanation = build_explanation(
        adjusted, contributors, occupied, adaptive_reason
    )
    result = {
        "node_id": reading.node_id,
        "timestamp": reading.timestamp.isoformat(),
        "raw_tier": raw_tier,
        "adjusted_tier": adjusted,
        "risk_score": round(float(score), 4),
        "confidence": confidence,
        "occupied": occupied,
        "prediction_source": source,
        "explanation_method": explanation_method,
        "explanation": explanation,
        "contributors": contributors[:4],
        "probabilities": probabilities,
        "window_size": len(window),
        "sequence_ready": len(window) >= SEQUENCE_LENGTH
    }
    latency = round((time.perf_counter() - started) * 1000.0, 3)
    result["latency_ms"] = latency
    result["event_id"] = save_event(reading, result, latency)
    return result

@app.get("/nodes")
def get_nodes():
    return nodes()

@app.get("/nodes/{node_id}/status")
def get_status(node_id: str):
    result = latest(node_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No readings found for this node")
    result["window_size"] = windows.size(node_id)
    result["sequence_ready"] = windows.size(node_id) >= SEQUENCE_LENGTH
    result["model_loaded"] = ml_service.ready
    return result

@app.get("/nodes/{node_id}/history")
def get_history(node_id: str, limit: int = Query(default=100, ge=1, le=1000)):
    return history(node_id, limit)

@app.get("/metrics/summary")
def get_metrics():
    result = metrics()
    result["model_loaded"] = ml_service.ready
    return result

if DASHBOARD_DIR.exists():
    app.mount("/", StaticFiles(directory=DASHBOARD_DIR, html=True), name="dashboard")
