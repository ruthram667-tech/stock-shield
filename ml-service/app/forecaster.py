"""
Stock Shield — ML Forecaster
Prophet/ARIMA models for consumption velocity and dynamic reorder point computation.
"""

import logging
import math
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ─── Model Storage ───────────────────────────────────────────────────────────

_trained_models: Dict[str, dict] = {}
_last_retrain: Optional[datetime] = None


def get_trained_model_count() -> int:
    return len(_trained_models)


def get_last_retrain() -> Optional[datetime]:
    return _last_retrain


def get_model_info(item_id: str) -> Optional[dict]:
    return _trained_models.get(item_id)


# ─── Core Forecasting ────────────────────────────────────────────────────────

def forecast_item(
    df: pd.DataFrame,
    item_id: str,
    lead_time_days: int = 3,
    service_level: float = 0.95,
    forecast_horizon_days: int = 7
) -> dict:
    """
    Fit a forecasting model and compute dynamic reorder point.

    Strategy:
    - If enough seasonal data (>= 48 hourly points), use Prophet
    - Otherwise, fall back to ARIMA (via pmdarima.auto_arima)
    - If too little data (< 24 points), use simple moving average

    Returns dict with: reorder_point, avg_daily_demand, safety_stock, model_used, etc.
    """
    if df.empty or len(df) < 10:
        logger.warning(f"Insufficient data for {item_id} ({len(df)} points), using defaults")
        return _default_result(item_id)

    # Calculate consumption (weight decreases over time = consumption)
    # We need the rate of decrease, not the absolute weight
    df = df.copy()
    df = df.sort_values("ds").reset_index(drop=True)

    # Compute hourly consumption (positive = consumed)
    df["consumption"] = -df["y"].diff()
    df["consumption"] = df["consumption"].clip(lower=0)  # Ignore restocks (weight increases)
    df = df.dropna(subset=["consumption"])

    if len(df) < 10:
        return _default_result(item_id)

    try:
        if len(df) >= 48:
            result = _forecast_prophet(df, item_id, lead_time_days, service_level, forecast_horizon_days)
        else:
            result = _forecast_arima(df, item_id, lead_time_days, service_level, forecast_horizon_days)
    except Exception as e:
        logger.error(f"Model fitting failed for {item_id}: {e}, falling back to SMA")
        result = _forecast_sma(df, item_id, lead_time_days, service_level)

    # Cache trained model info
    _trained_models[item_id] = {
        "model_type": result["model_used"],
        "mae": result.get("mae", 0),
        "rmse": result.get("rmse", 0),
        "last_trained": datetime.now(timezone.utc),
        "data_points_used": len(df)
    }
    global _last_retrain
    _last_retrain = datetime.now(timezone.utc)

    return result


def _forecast_prophet(df, item_id, lead_time_days, service_level, forecast_horizon_days):
    """Use Facebook Prophet for items with enough data."""
    from prophet import Prophet

    # Prepare Prophet input (ds, y = hourly consumption)
    prophet_df = df[["ds", "consumption"]].rename(columns={"consumption": "y"})

    model = Prophet(
        daily_seasonality=True,
        weekly_seasonality=True if len(prophet_df) >= 168 else False,  # Need 1 week of data
        yearly_seasonality=False,
        changepoint_prior_scale=0.05,
        interval_width=service_level
    )
    model.fit(prophet_df)

    # Forecast
    future = model.make_future_dataframe(periods=forecast_horizon_days * 24, freq="h")
    forecast = model.predict(future)

    # Average hourly demand → daily demand
    avg_hourly = forecast["yhat"].tail(forecast_horizon_days * 24).mean()
    avg_daily_demand = max(0, avg_hourly * 24)

    # Standard deviation of demand
    demand_std = df["consumption"].std()

    # Safety stock: Z * σ_demand * sqrt(lead_time)
    z_score = _z_score(service_level)
    safety_stock = z_score * demand_std * 24 * math.sqrt(lead_time_days)

    # Reorder Point = (avg_daily_demand * lead_time) + safety_stock
    reorder_point = (avg_daily_demand * lead_time_days) + safety_stock

    # Accuracy metrics (in-sample)
    merged = prophet_df.merge(forecast[["ds", "yhat"]], on="ds", how="inner")
    mae = (merged["y"] - merged["yhat"]).abs().mean()
    rmse = math.sqrt(((merged["y"] - merged["yhat"]) ** 2).mean())

    # Build forecast points for API response
    forecast_points = []
    future_forecast = forecast.tail(forecast_horizon_days * 24)
    for _, row in future_forecast.iterrows():
        forecast_points.append({
            "timestamp": row["ds"].isoformat(),
            "predicted_weight": max(0, row["yhat"]),
            "lower_bound": max(0, row["yhat_lower"]),
            "upper_bound": row["yhat_upper"]
        })

    return {
        "item_id": item_id,
        "reorder_point": round(reorder_point, 3),
        "avg_daily_demand": round(avg_daily_demand, 3),
        "safety_stock": round(safety_stock, 3),
        "model_used": "prophet",
        "confidence": service_level,
        "forecast_horizon_days": forecast_horizon_days,
        "forecast": forecast_points,
        "mae": round(mae, 4),
        "rmse": round(rmse, 4)
    }


def _forecast_arima(df, item_id, lead_time_days, service_level, forecast_horizon_days):
    """Use AutoARIMA for shorter time series."""
    import pmdarima as pm

    series = df["consumption"].values

    model = pm.auto_arima(
        series,
        seasonal=False,
        stepwise=True,
        suppress_warnings=True,
        error_action="ignore",
        max_order=5
    )

    # Forecast
    n_periods = forecast_horizon_days * 24
    forecast_values, conf_int = model.predict(n_periods=n_periods, return_conf_int=True, alpha=1 - service_level)

    avg_hourly = np.mean(forecast_values)
    avg_daily_demand = max(0, avg_hourly * 24)

    demand_std = np.std(series)
    z_score = _z_score(service_level)
    safety_stock = z_score * demand_std * 24 * math.sqrt(lead_time_days)
    reorder_point = (avg_daily_demand * lead_time_days) + safety_stock

    # In-sample metrics
    in_sample_pred = model.predict_in_sample()
    residuals = series[len(series) - len(in_sample_pred):] - in_sample_pred
    mae = np.mean(np.abs(residuals))
    rmse = math.sqrt(np.mean(residuals ** 2))

    return {
        "item_id": item_id,
        "reorder_point": round(reorder_point, 3),
        "avg_daily_demand": round(avg_daily_demand, 3),
        "safety_stock": round(safety_stock, 3),
        "model_used": "arima",
        "confidence": service_level,
        "forecast_horizon_days": forecast_horizon_days,
        "forecast": None,
        "mae": round(float(mae), 4),
        "rmse": round(float(rmse), 4)
    }


def _forecast_sma(df, item_id, lead_time_days, service_level):
    """Simple moving average fallback for very sparse data."""
    avg_hourly = df["consumption"].mean()
    avg_daily = max(0, avg_hourly * 24)
    demand_std = df["consumption"].std()

    z_score = _z_score(service_level)
    safety_stock = z_score * demand_std * 24 * math.sqrt(lead_time_days)
    reorder_point = (avg_daily * lead_time_days) + safety_stock

    return {
        "item_id": item_id,
        "reorder_point": round(reorder_point, 3),
        "avg_daily_demand": round(avg_daily, 3),
        "safety_stock": round(safety_stock, 3),
        "model_used": "sma",
        "confidence": service_level,
        "forecast_horizon_days": 7,
        "forecast": None,
        "mae": None,
        "rmse": None
    }


def _default_result(item_id):
    return {
        "item_id": item_id,
        "reorder_point": 3.0,
        "avg_daily_demand": 1.0,
        "safety_stock": 1.5,
        "model_used": "default",
        "confidence": 0.0,
        "forecast_horizon_days": 7,
        "forecast": None,
        "mae": None,
        "rmse": None
    }


def _z_score(service_level: float) -> float:
    """Convert service level to Z-score for safety stock calculation."""
    from scipy.stats import norm
    return norm.ppf(service_level)
