"""
Stock Shield — ML Service
FastAPI application for demand forecasting, dynamic threshold derivation,
and universal multi-tenant custom model training.
"""

import io
import logging
from contextlib import asynccontextmanager
from typing import List, Dict, Any

import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    PredictRequest, BatchPredictRequest,
    PredictionResponse, BatchPredictionResponse,
    HealthResponse, ModelMetrics,
    TrainModelRequest, TrainModelResponse,
    GenericPredictRequest, GenericPredictionResponse,
    ModelSummary
)
from .influx_client import InfluxClient
from .model_store import model_store
from .forecaster import (
    forecast_item,
    train_universal_sensor_model,
    predict_universal_sensor,
    get_trained_model_count,
    get_last_retrain,
    get_model_info
)
from .scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

influx = InfluxClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    logger.info("🚀 Universal Stock Shield ML Service starting...")
    start_scheduler()
    yield
    logger.info("🛑 Shutting down ML Service...")
    stop_scheduler()
    influx.close()


app = FastAPI(
    title="Stock Shield Universal ML Service",
    description="Universal AI model training and anomaly/demand forecasting for any sensor and industry",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Universal Multi-Tenant Training & Forecasting Endpoints ─────────────────

@app.post("/train/{tenant_id}/{sensor_type}", response_model=TrainModelResponse)
async def train_custom_sensor_model(
    tenant_id: str,
    sensor_type: str,
    request: TrainModelRequest
):
    """
    Train a custom model on the user's OWN telemetry data for ANY sensor type.
    Pulls data from InfluxDB for this tenant, learns distribution & patterns,
    computes learned thresholds, and persists the model.
    """
    df = influx.get_sensor_history(
        tenant_id=tenant_id,
        sensor_type=sensor_type,
        range_str=request.training_window
    )

    if df.empty or len(df) < 5:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough data in InfluxDB for {tenant_id}/{sensor_type} in window {request.training_window}. Found {len(df)} points. Minimum 5 required, or upload historical CSV first."
        )

    try:
        result = train_universal_sensor_model(
            df=df,
            tenant_id=tenant_id,
            sensor_type=sensor_type,
            training_window=request.training_window,
            service_level=request.service_level,
            lead_time_days=request.lead_time_days
        )
        return result
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise HTTPException(status_code=500, detail=f"Training error: {str(e)}")


@app.post("/predict/{tenant_id}/{sensor_type}", response_model=GenericPredictionResponse)
async def predict_custom_sensor(
    tenant_id: str,
    sensor_type: str,
    request: GenericPredictRequest
):
    """
    Generate forecast points and evaluate anomaly detection using
    the tenant's OWN trained model for this sensor type.
    """
    df_recent = influx.get_sensor_history(
        tenant_id=tenant_id,
        sensor_type=sensor_type,
        range_str="7d"
    )

    try:
        result = predict_universal_sensor(
            tenant_id=tenant_id,
            sensor_type=sensor_type,
            df_recent=df_recent,
            horizon_hours=request.horizon_hours,
            service_level=request.service_level
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload/{tenant_id}/{sensor_type}")
async def upload_training_csv(
    tenant_id: str,
    sensor_type: str,
    file: UploadFile = File(...)
):
    """
    Allow users to upload historical CSV telemetry data for any sensor type.
    CSV must contain headers: ('timestamp' or 'ds') and ('value' or 'y').
    Optional 'locationId' column.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))

        # Check column names
        valid_ts = "timestamp" in df.columns or "ds" in df.columns
        valid_val = "value" in df.columns or "y" in df.columns

        if not valid_ts or not valid_val:
            raise HTTPException(
                status_code=400,
                detail=f"CSV must contain timestamp ('timestamp' or 'ds') and value ('value' or 'y') columns. Found columns: {list(df.columns)}"
            )

        rows_written = influx.write_batch(
            tenant_id=tenant_id,
            sensor_type=sensor_type,
            df=df
        )

        return {
            "status": "success",
            "tenant_id": tenant_id,
            "sensor_type": sensor_type,
            "rows_imported": rows_written,
            "message": f"Successfully imported {rows_written} data points for training."
        }
    except Exception as e:
        logger.error(f"CSV upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process CSV: {str(e)}")


@app.get("/models/{tenant_id}", response_model=List[Dict[str, Any]])
async def list_tenant_models(tenant_id: str):
    """List all custom-trained models for a specific tenant."""
    return model_store.list_models_for_tenant(tenant_id)


@app.get("/models/{tenant_id}/{sensor_type}")
async def get_tenant_model_details(tenant_id: str, sensor_type: str):
    """Get metadata and learned thresholds for a specific tenant sensor model."""
    meta = model_store.get_metadata(tenant_id, sensor_type)
    thresh = model_store.get_thresholds(tenant_id, sensor_type)
    if not meta:
        raise HTTPException(status_code=404, detail="No trained model found for this sensor type.")
    return {
        "metadata": meta,
        "thresholds": thresh
    }


# ─── Legacy Endpoints (Backward Compatible) ──────────────────────────────────

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
    """Legacy: On-demand forecast for a single inventory item."""
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
    """Legacy: Batch forecast for multiple inventory items."""
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
    """Legacy: Get accuracy metrics for an inventory model."""
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
