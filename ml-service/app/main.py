"""
Stock Shield — ML Service
FastAPI application for demand forecasting and dynamic reorder point computation.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    PredictRequest, BatchPredictRequest,
    PredictionResponse, BatchPredictionResponse,
    HealthResponse, ModelMetrics
)
from .influx_client import InfluxClient
from .forecaster import forecast_item, get_trained_model_count, get_last_retrain, get_model_info
from .scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

influx = InfluxClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    logger.info("🚀 Stock Shield ML Service starting...")
    start_scheduler()
    yield
    logger.info("🛑 Shutting down ML Service...")
    stop_scheduler()
    influx.close()


app = FastAPI(
    title="Stock Shield ML Service",
    description="Demand forecasting and dynamic reorder point computation for inventory management",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Service health check."""
    return HealthResponse(
        status="healthy",
        influxdb_connected=influx.is_connected(),
        models_loaded=get_trained_model_count(),
        last_retrain=get_last_retrain()
    )


@app.post("/predict/{item_id}", response_model=PredictionResponse)
async def predict_single(item_id: str, request: PredictRequest):
    """
    On-demand forecast for a single item.
    Pulls history from InfluxDB, fits model, returns prediction + reorder point.
    """
    df = influx.get_weight_history(item_id, range_str="30d")

    if df.empty:
        raise HTTPException(status_code=404, detail=f"No telemetry data found for item {item_id}")

    result = forecast_item(
        df=df,
        item_id=item_id,
        lead_time_days=request.lead_time_days,
        service_level=request.service_level
    )

    return PredictionResponse(
        item_id=result["item_id"],
        reorder_point=result["reorder_point"],
        avg_daily_demand=result["avg_daily_demand"],
        safety_stock=result["safety_stock"],
        model_used=result["model_used"],
        confidence=result["confidence"],
        forecast_horizon_days=result["forecast_horizon_days"],
        forecast=result.get("forecast"),
        mae=result.get("mae"),
        rmse=result.get("rmse")
    )


@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch(request: BatchPredictRequest):
    """
    Batch forecast for multiple items.
    """
    predictions = []
    failed = 0

    for item_id in request.items:
        try:
            df = influx.get_weight_history(item_id, range_str="30d")
            result = forecast_item(
                df=df,
                item_id=item_id,
                lead_time_days=request.lead_time_days,
                service_level=request.service_level
            )

            predictions.append(PredictionResponse(
                item_id=result["item_id"],
                reorder_point=result["reorder_point"],
                avg_daily_demand=result["avg_daily_demand"],
                safety_stock=result["safety_stock"],
                model_used=result["model_used"],
                confidence=result["confidence"],
                forecast_horizon_days=result["forecast_horizon_days"],
                mae=result.get("mae"),
                rmse=result.get("rmse")
            ))
        except Exception as e:
            logger.error(f"Batch prediction failed for {item_id}: {e}")
            failed += 1

    return BatchPredictionResponse(
        predictions=predictions,
        processed=len(predictions),
        failed=failed
    )


@app.get("/models/{item_id}/metrics", response_model=ModelMetrics)
async def get_metrics(item_id: str):
    """Get accuracy metrics for a trained model."""
    info = get_model_info(item_id)
    if info is None:
        raise HTTPException(status_code=404, detail=f"No trained model found for item {item_id}")

    return ModelMetrics(
        item_id=item_id,
        model_type=info["model_type"],
        mae=info["mae"],
        rmse=info["rmse"],
        last_trained=info["last_trained"],
        data_points_used=info["data_points_used"]
    )
