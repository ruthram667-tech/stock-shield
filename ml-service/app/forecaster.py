"""
Stock Shield — ML Forecaster & Universal Custom Model Trainer
Supports:
1. Dynamic consumption forecasting for inventory (Prophet / ARIMA / SMA)
2. Universal custom model training on ANY sensor type (temperature, humidity,
   pressure, pH, vibration, gas, moisture, RPM, etc.) for ANY tenant.
"""

import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple

import numpy as np
import pandas as pd

from .model_store import model_store

logger = logging.getLogger(__name__)

# Legacy in-memory cache for backwards compatibility
_trained_models: Dict[str, dict] = {}
_last_retrain: Optional[datetime] = None


def get_trained_model_count() -> int:
    return len(_trained_models) + len(model_store.list_all_models())


def get_last_retrain() -> Optional[datetime]:
    return _last_retrain


def get_model_info(item_id: str) -> Optional[dict]:
    return _trained_models.get(item_id)


# ─── Universal Model Training (Any Industry, Any Sensor) ─────────────────────

def analyze_time_series(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze time-series characteristics to select the best algorithm."""
    y = df["y"].values
    n = len(y)

    mean_val = float(np.mean(y))
    std_val = float(np.std(y)) if n > 1 else 0.0
    min_val = float(np.min(y))
    max_val = float(np.max(y))

    # Detect trend via simple linear regression slope
    x = np.arange(n)
    if n > 1 and std_val > 0:
        slope = float(np.polyfit(x, y, 1)[0])
    else:
        slope = 0.0

    # Detect 24h seasonality if we have enough hourly samples
    has_seasonality = False
    if n >= 48:
        try:
            # Autocorrelation at lag 24
            series = pd.Series(y)
            autocorr_24 = series.autocorr(lag=24)
            if not np.isnan(autocorr_24) and autocorr_24 > 0.3:
                has_seasonality = True
        except Exception:
            pass

    return {
        "n": n,
        "mean": mean_val,
        "std": std_val,
        "min": min_val,
        "max": max_val,
        "slope": slope,
        "has_seasonality": has_seasonality
    }


def compute_learned_thresholds(analysis: Dict[str, Any], service_level: float = 0.95) -> Dict[str, Any]:
    """Derive learned operational thresholds and critical limits from real telemetry distribution."""
    mean_val = analysis["mean"]
    std_val = max(analysis["std"], 1e-4)

    z = _z_score(service_level)
    z_crit = _z_score(min(0.999, service_level + 0.04))

    min_safe = round(mean_val - z * std_val, 2)
    max_safe = round(mean_val + z * std_val, 2)
    critical_min = round(mean_val - z_crit * std_val, 2)
    critical_max = round(mean_val + z_crit * std_val, 2)

    return {
        "min_safe": min_safe,
        "max_safe": max_safe,
        "critical_min": critical_min,
        "critical_max": critical_max,
        "mean": round(mean_val, 3),
        "std_dev": round(std_val, 3)
    }


def train_universal_sensor_model(
    df: pd.DataFrame,
    tenant_id: str,
    sensor_type: str,
    training_window: str = "30d",
    service_level: float = 0.95,
    lead_time_days: int = 3
) -> Dict[str, Any]:
    """
    Train a custom model on the user's OWN telemetry data for ANY sensor type.
    Learns patterns, drift, seasonality, and sets statistical boundaries.
    """
    if df.empty or len(df) < 5:
        raise ValueError(f"Insufficient data points ({len(df)}) to train model for {sensor_type}. At least 5 points required.")

    df = df.copy().sort_values("ds").reset_index(drop=True)
    analysis = analyze_time_series(df)
    thresholds = compute_learned_thresholds(analysis, service_level)

    model_type = "statistical_baseline"
    model_artifact = None
    mae = 0.0
    rmse = 0.0

    # 1. Try Prophet if sufficient points and seasonality
    if analysis["n"] >= 48 and analysis["has_seasonality"]:
        try:
            from prophet import Prophet
            prophet_df = df[["ds", "y"]].copy()
            model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True if analysis["n"] >= 168 else False,
                yearly_seasonality=False,
                interval_width=service_level
            )
            model.fit(prophet_df)
            forecast = model.predict(prophet_df)
            diff = (prophet_df["y"] - forecast["yhat"]).values
            mae = float(np.mean(np.abs(diff)))
            rmse = float(np.sqrt(np.mean(diff ** 2)))
            model_type = "prophet"
            model_artifact = model
        except Exception as e:
            logger.warning(f"Prophet fitting failed: {e}. Trying ARIMA.")

    # 2. Try AutoARIMA if Prophet was not used or failed
    if model_artifact is None and analysis["n"] >= 24:
        try:
            import pmdarima as pm
            y_vals = df["y"].values
            model = pm.auto_arima(
                y_vals,
                seasonal=False,
                stepwise=True,
                suppress_warnings=True,
                error_action="ignore",
                max_order=5
            )
            in_sample = model.predict_in_sample()
            residuals = y_vals[-len(in_sample):] - in_sample
            mae = float(np.mean(np.abs(residuals)))
            rmse = float(np.sqrt(np.mean(residuals ** 2)))
            model_type = "arima"
            model_artifact = model
        except Exception as e:
            logger.warning(f"AutoARIMA fitting failed: {e}. Falling back to linear trend / baseline.")

    # 3. Fallback: Moving average + Trend model
    if model_artifact is None:
        y_vals = df["y"].values
        rolling_mean = pd.Series(y_vals).rolling(window=min(5, len(y_vals)), min_periods=1).mean().values
        diff = y_vals - rolling_mean
        mae = float(np.mean(np.abs(diff)))
        rmse = float(np.sqrt(np.mean(diff ** 2)))
        model_type = "trend_baseline"
        model_artifact = {
            "mean": analysis["mean"],
            "std": analysis["std"],
            "slope": analysis["slope"],
            "last_value": float(y_vals[-1])
        }

    trained_at = datetime.now(timezone.utc).isoformat()

    metadata = {
        "tenant_id": tenant_id,
        "sensor_type": sensor_type,
        "model_type": model_type,
        "training_window": training_window,
        "service_level": service_level,
        "data_points_used": analysis["n"],
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "trained_at": trained_at,
        "last_trained": trained_at,
        "analysis": analysis
    }

    # Save to disk
    model_store.save_model(
        tenant_id=tenant_id,
        sensor_type=sensor_type,
        model_artifact=model_artifact,
        metadata=metadata,
        thresholds=thresholds
    )

    global _last_retrain
    _last_retrain = datetime.now(timezone.utc)

    return {
        "tenant_id": tenant_id,
        "sensor_type": sensor_type,
        "model_type": model_type,
        "data_points_used": analysis["n"],
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "trained_at": trained_at,
        "learned_thresholds": thresholds,
        "status": "success",
        "message": f"Successfully trained custom {model_type} model on {analysis['n']} data points."
    }


def predict_universal_sensor(
    tenant_id: str,
    sensor_type: str,
    df_recent: pd.DataFrame,
    horizon_hours: int = 24,
    service_level: float = 0.95
) -> Dict[str, Any]:
    """
    Generate forecast points using the tenant's OWN custom trained model.
    """
    model_artifact = model_store.load_model(tenant_id, sensor_type)
    metadata = model_store.get_metadata(tenant_id, sensor_type)
    thresholds = model_store.get_thresholds(tenant_id, sensor_type)

    if model_artifact is None or metadata is None:
        raise ValueError(f"No trained model exists for tenant={tenant_id}, sensor={sensor_type}. Please call /train first.")

    model_type = metadata.get("model_type", "trend_baseline")
    forecast_points: List[Dict[str, Any]] = []

    latest_time = datetime.now(timezone.utc)
    latest_val = float(df_recent["y"].iloc[-1]) if not df_recent.empty else thresholds.get("mean", 0.0)

    std_val = thresholds.get("std_dev", 1.0)
    z = _z_score(service_level)

    # 1. Prophet prediction
    if model_type == "prophet":
        try:
            future = model_artifact.make_future_dataframe(periods=horizon_hours, freq="h")
            pred = model_artifact.predict(future).tail(horizon_hours)
            for _, row in pred.iterrows():
                forecast_points.append({
                    "timestamp": row["ds"].isoformat(),
                    "predicted_value": round(float(row["yhat"]), 3),
                    "lower_bound": round(float(row["yhat_lower"]), 3),
                    "upper_bound": round(float(row["yhat_upper"]), 3)
                })
        except Exception as e:
            logger.warning(f"Prophet prediction failed: {e}, falling back to trend.")

    # 2. ARIMA prediction
    elif model_type == "arima":
        try:
            forecast_values, conf_int = model_artifact.predict(
                n_periods=horizon_hours, return_conf_int=True, alpha=1 - service_level
            )
            for i, val in enumerate(forecast_values):
                ts = (latest_time + timedelta(hours=i + 1)).isoformat()
                forecast_points.append({
                    "timestamp": ts,
                    "predicted_value": round(float(val), 3),
                    "lower_bound": round(float(conf_int[i][0]), 3),
                    "upper_bound": round(float(conf_int[i][1]), 3)
                })
        except Exception as e:
            logger.warning(f"ARIMA prediction failed: {e}, falling back to trend.")

    # 3. Baseline / Trend fallback
    if not forecast_points:
        slope = metadata.get("analysis", {}).get("slope", 0.0)
        for i in range(1, horizon_hours + 1):
            ts = (latest_time + timedelta(hours=i)).isoformat()
            pred_val = latest_val + (slope * i)
            forecast_points.append({
                "timestamp": ts,
                "predicted_value": round(float(pred_val), 3),
                "lower_bound": round(float(pred_val - z * std_val), 3),
                "upper_bound": round(float(pred_val + z * std_val), 3)
            })

    pred_vals = [p["predicted_value"] for p in forecast_points]
    predicted_mean = round(float(np.mean(pred_vals)), 3)
    predicted_min = round(float(np.min(pred_vals)), 3)
    predicted_max = round(float(np.max(pred_vals)), 3)

    # Detect anomaly in latest reading
    anomaly_detected = False
    if thresholds:
        min_safe = thresholds.get("min_safe")
        max_safe = thresholds.get("max_safe")
        if min_safe is not None and latest_val < min_safe:
            anomaly_detected = True
        if max_safe is not None and latest_val > max_safe:
            anomaly_detected = True

    return {
        "tenant_id": tenant_id,
        "sensor_type": sensor_type,
        "model_used": model_type,
        "forecast_horizon_hours": horizon_hours,
        "forecast": forecast_points,
        "latest_reading": round(latest_val, 3),
        "predicted_mean": predicted_mean,
        "predicted_min": predicted_min,
        "predicted_max": predicted_max,
        "anomaly_detected": anomaly_detected,
        "status": "success"
    }


# ─── Legacy Forecasting (Inventory Reorder Points) ───────────────────────────

def forecast_item(
    df: pd.DataFrame,
    item_id: str,
    lead_time_days: int = 3,
    service_level: float = 0.95,
    forecast_horizon_days: int = 7
) -> dict:
    """Legacy inventory stock depletion forecasting."""
    if df.empty or len(df) < 10:
        logger.warning(f"Insufficient data for {item_id} ({len(df)} points), using defaults")
        return _default_result(item_id)

    df = df.copy()
    df = df.sort_values("ds").reset_index(drop=True)
    df["consumption"] = -df["y"].diff()
    df["consumption"] = df["consumption"].clip(lower=0)
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
    from prophet import Prophet
    prophet_df = df[["ds", "consumption"]].rename(columns={"consumption": "y"})
    model = Prophet(
        daily_seasonality=True,
        weekly_seasonality=True if len(prophet_df) >= 168 else False,
        yearly_seasonality=False,
        changepoint_prior_scale=0.05,
        interval_width=service_level
    )
    model.fit(prophet_df)

    future = model.make_future_dataframe(periods=forecast_horizon_days * 24, freq="h")
    forecast = model.predict(future)

    avg_hourly = forecast["yhat"].tail(forecast_horizon_days * 24).mean()
    avg_daily_demand = max(0, avg_hourly * 24)
    demand_std = df["consumption"].std()

    z_score = _z_score(service_level)
    safety_stock = z_score * demand_std * 24 * math.sqrt(lead_time_days)
    reorder_point = (avg_daily_demand * lead_time_days) + safety_stock

    merged = prophet_df.merge(forecast[["ds", "yhat"]], on="ds", how="inner")
    mae = (merged["y"] - merged["yhat"]).abs().mean()
    rmse = math.sqrt(((merged["y"] - merged["yhat"]) ** 2).mean())

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

    n_periods = forecast_horizon_days * 24
    forecast_values, conf_int = model.predict(n_periods=n_periods, return_conf_int=True, alpha=1 - service_level)

    avg_hourly = np.mean(forecast_values)
    avg_daily_demand = max(0, avg_hourly * 24)
    demand_std = np.std(series)
    z_score = _z_score(service_level)
    safety_stock = z_score * demand_std * 24 * math.sqrt(lead_time_days)
    reorder_point = (avg_daily_demand * lead_time_days) + safety_stock

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
    from scipy.stats import norm
    return norm.ppf(service_level)
