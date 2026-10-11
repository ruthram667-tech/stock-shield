"""
Stock Shield — ML Service
Pydantic models for API request/response validation.
Supports both legacy inventory forecasting and universal multi-tenant sensor training.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ─── Legacy Request Models ───────────────────────────────────────────────────

class PredictRequest(BaseModel):
    lead_time_days: int = Field(default=3, ge=1, le=30, description="Supplier lead time in days")
    service_level: float = Field(default=0.95, ge=0.5, le=0.99, description="Desired service level (probability)")


class BatchPredictRequest(BaseModel):
    items: List[str] = Field(..., description="List of item IDs to forecast")
    lead_time_days: int = Field(default=3, ge=1, le=30)
    service_level: float = Field(default=0.95, ge=0.5, le=0.99)


# ─── Universal Multi-Tenant Sensor Model Requests ────────────────────────────

class TrainModelRequest(BaseModel):
    training_window: str = Field(default="30d", description="InfluxDB range window e.g. 7d, 30d, 90d")
    service_level: float = Field(default=0.95, ge=0.5, le=0.99, description="Confidence interval")
    seasonality_mode: Optional[str] = Field(default="auto", description="auto, daily, weekly, additive, multiplicative")
    lead_time_days: int = Field(default=3, ge=1, le=30)


class GenericPredictRequest(BaseModel):
    horizon_hours: int = Field(default=24, ge=1, le=720, description="Forecast horizon in hours")
    service_level: float = Field(default=0.95, ge=0.5, le=0.99)


# ─── Response Models ─────────────────────────────────────────────────────────

class ForecastPoint(BaseModel):
    timestamp: str
    predicted_value: float
    lower_bound: float
    upper_bound: float


class PredictionResponse(BaseModel):
    item_id: str
    reorder_point: float
    avg_daily_demand: float
    safety_stock: float
    model_used: str  # "prophet", "arima", etc.
    confidence: float
    forecast_horizon_days: int
    forecast: Optional[List[Dict[str, Any]]] = None
    mae: Optional[float] = None
    rmse: Optional[float] = None


class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]
    processed: int
    failed: int


class LearnedThresholds(BaseModel):
    min_safe: Optional[float] = None
    max_safe: Optional[float] = None
    critical_min: Optional[float] = None
    critical_max: Optional[float] = None
    mean: float
    std_dev: float


class TrainModelResponse(BaseModel):
    tenant_id: str
    sensor_type: str
    model_type: str
    data_points_used: int
    mae: float
    rmse: float
    trained_at: str
    learned_thresholds: LearnedThresholds
    status: str
    message: str


class GenericPredictionResponse(BaseModel):
    tenant_id: str
    sensor_type: str
    model_used: str
    forecast_horizon_hours: int
    forecast: List[ForecastPoint]
    latest_reading: Optional[float] = None
    predicted_mean: float
    predicted_min: float
    predicted_max: float
    anomaly_detected: bool
    status: str


class ModelSummary(BaseModel):
    tenant_id: str
    sensor_type: str
    model_type: str
    mae: float
    rmse: float
    last_trained: str
    data_points_used: int
    learned_thresholds: Optional[Dict[str, Any]] = None


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
