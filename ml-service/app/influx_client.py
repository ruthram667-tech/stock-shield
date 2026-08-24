"""
Stock Shield — InfluxDB Client
Wrapper for querying time-series telemetry data from InfluxDB.
"""

import os
import logging
from typing import List, Optional
from datetime import datetime

import pandas as pd
from influxdb_client import InfluxDBClient

logger = logging.getLogger(__name__)

INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "changeme_influx_token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "stockshield")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "telemetry")


class InfluxClient:
    """Manages connection to InfluxDB and provides query methods for ML pipeline."""

    def __init__(self):
        self.client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        self.query_api = self.client.query_api()
        self.bucket = INFLUXDB_BUCKET
        self.org = INFLUXDB_ORG

    def is_connected(self) -> bool:
        """Check if InfluxDB is reachable."""
        try:
            health = self.client.health()
            return health.status == "pass"
        except Exception:
            return False

    def get_weight_history(self, item_id: str, range_str: str = "30d") -> pd.DataFrame:
        """
        Fetch weight history for a specific item.
        Returns a DataFrame with columns: [ds, y] (Prophet-compatible naming).
        """
        flux = f'''
        from(bucket: "{self.bucket}")
            |> range(start: -{range_str})
            |> filter(fn: (r) => r._measurement == "weight")
            |> filter(fn: (r) => r.itemId == "{item_id}")
            |> filter(fn: (r) => r._field == "value")
            |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
        '''

        try:
            tables = self.query_api.query(flux, org=self.org)
            records = []
            for table in tables:
                for record in table.records:
                    records.append({
                        "ds": record.get_time(),
                        "y": record.get_value()
                    })

            if not records:
                logger.warning(f"No weight data found for item {item_id}")
                return pd.DataFrame(columns=["ds", "y"])

            df = pd.DataFrame(records)
            df["ds"] = pd.to_datetime(df["ds"])
            df = df.sort_values("ds").reset_index(drop=True)
            return df

        except Exception as e:
            logger.error(f"InfluxDB query failed for item {item_id}: {e}")
            return pd.DataFrame(columns=["ds", "y"])

    def get_all_item_ids(self) -> List[str]:
        """Fetch all unique item IDs that have telemetry data."""
        flux = f'''
        from(bucket: "{self.bucket}")
            |> range(start: -7d)
            |> filter(fn: (r) => r._measurement == "weight")
            |> keep(columns: ["itemId"])
            |> distinct(column: "itemId")
        '''

        try:
            tables = self.query_api.query(flux, org=self.org)
            item_ids = set()
            for table in tables:
                for record in table.records:
                    val = record.values.get("itemId")
                    if val:
                        item_ids.add(val)
            return list(item_ids)
        except Exception as e:
            logger.error(f"Failed to fetch item IDs: {e}")
            return []

    def close(self):
        """Close the InfluxDB client connection."""
        self.client.close()
