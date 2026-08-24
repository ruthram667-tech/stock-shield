"""
Stock Shield — ML Service
Pydantic models for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ─── Request Models ──────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    lead_time_days: int = Field(default=3, ge=1, le=30, description="Supplier lead time in days")
    service_level: float = Field(default=0.95, ge=0.5, le=0.99, description="Desired service level (probability)")


class BatchPredictRequest(BaseModel):
    items: List[str] = Field(..., description="List of item IDs to forecast")
    lead_time_days: int = Field(default=3, ge=1, le=30)
    service_level: float = Field(default=0.95, ge=0.5, le=0.99)


# ─── Response Models ─────────────────────────────────────────────────────────

class ForecastPoint(BaseModel):
    timestamp: datetime
    predicted_weight: float
    lower_bound: float
    upper_bound: float


class PredictionResponse(BaseModel):
    item_id: str
    reorder_point: float
    avg_daily_demand: float
    safety_stock: float
    model_used: str  # "prophet" or "arima"
    confidence: float
    forecast_horizon_days: int
    forecast: Optional[List[ForecastPoint]] = None
    mae: Optional[float] = None
    rmse: Optional[float] = None


class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]
    processed: int
    failed: int


# ─── Threshold Push (sent to Java backend) ───────────────────────────────────

class ThresholdItem(BaseModel):
    itemId: str
    reorderPoint: float
    confidence: float
    model: str
    forecastHorizon: int


class ThresholdUpdatePayload(BaseModel):
    items: List[ThresholdItem]


# ─── Health Check ─────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    influxdb_connected: bool
    models_loaded: int
    last_retrain: Optional[datetime] = None


class ModelMetrics(BaseModel):
    item_id: str
    model_type: str
    mae: float
    rmse: float
    last_trained: datetime
    data_points_used: int
