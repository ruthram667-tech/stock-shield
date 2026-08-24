"""
Stock Shield — ML Scheduler
Periodic retraining and threshold push to Java backend.
"""

import os
import logging
from datetime import datetime, timezone

import httpx
from apscheduler.schedulers.background import BackgroundScheduler

from .influx_client import InfluxClient
from .forecaster import forecast_item

logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")
RETRAIN_INTERVAL_HOURS = int(os.getenv("ML_RETRAIN_INTERVAL_HOURS", "6"))
DEFAULT_LEAD_TIME = int(os.getenv("ML_DEFAULT_LEAD_TIME_DAYS", "3"))
DEFAULT_SERVICE_LEVEL = float(os.getenv("ML_DEFAULT_SERVICE_LEVEL", "0.95"))

scheduler = BackgroundScheduler()


def retrain_and_push():
    """
    Retrain models for all items and push updated thresholds to the Java backend.
    This runs on a schedule (default: every 6 hours).
    """
    logger.info("🧠 Starting scheduled model retrain cycle...")
    influx = InfluxClient()

    try:
        item_ids = influx.get_all_item_ids()
        if not item_ids:
            logger.warning("No item IDs found in InfluxDB — skipping retrain")
            return

        threshold_items = []
        success_count = 0
        fail_count = 0

        for item_id in item_ids:
            try:
                df = influx.get_weight_history(item_id, range_str="30d")
                result = forecast_item(
                    df=df,
                    item_id=item_id,
                    lead_time_days=DEFAULT_LEAD_TIME,
                    service_level=DEFAULT_SERVICE_LEVEL
                )

                threshold_items.append({
                    "itemId": item_id,
                    "reorderPoint": result["reorder_point"],
                    "confidence": result["confidence"],
                    "model": result["model_used"],
                    "forecastHorizon": result["forecast_horizon_days"]
                })
                success_count += 1
                logger.info(f"  ✅ {item_id}: ROP={result['reorder_point']:.2f}kg "
                           f"(model={result['model_used']}, demand={result['avg_daily_demand']:.2f}kg/day)")

            except Exception as e:
                fail_count += 1
                logger.error(f"  ❌ Failed to forecast {item_id}: {e}")

        # Push thresholds to Java backend
        if threshold_items:
            _push_thresholds(threshold_items)

        logger.info(f"🧠 Retrain cycle complete: {success_count} succeeded, {fail_count} failed")

    finally:
        influx.close()


def _push_thresholds(items: list):
    """Push updated thresholds to the Java backend via REST."""
    url = f"{BACKEND_URL}/api/thresholds/update"
    payload = {"items": items}

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload)
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📤 Pushed {result.get('updated', 0)} threshold updates to backend")
            else:
                logger.error(f"Backend rejected threshold update: {response.status_code} {response.text}")
    except httpx.ConnectError:
        logger.error(f"Cannot connect to backend at {url} — thresholds NOT pushed")
    except Exception as e:
        logger.error(f"Failed to push thresholds: {e}")


def start_scheduler():
    """Start the background scheduler for periodic retraining."""
    scheduler.add_job(
        retrain_and_push,
        trigger="interval",
        hours=RETRAIN_INTERVAL_HOURS,
        id="retrain_models",
        name="Retrain ML models and push thresholds",
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc)  # Run immediately on startup
    )
    scheduler.start()
    logger.info(f"⏰ ML scheduler started — retrain every {RETRAIN_INTERVAL_HOURS}h")


def stop_scheduler():
    """Stop the background scheduler."""
    scheduler.shutdown(wait=False)
    logger.info("⏰ ML scheduler stopped")
