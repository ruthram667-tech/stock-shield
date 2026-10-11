"""
Stock Shield — InfluxDB Client
Wrapper for querying and writing time-series telemetry data from InfluxDB.
Supports any measurement/sensor type across all tenants.
"""

import os
import logging
from typing import List, Optional
from datetime import datetime, timezone

import pandas as pd
from influxdb_client import InfluxDBClient, Point, WritePrecision

logger = logging.getLogger(__name__)

INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "changeme_influx_token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "stockshield")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "telemetry")


class InfluxClient:
    """Manages connection to InfluxDB and provides query and write methods for ML pipeline."""

    def __init__(self):
        self.client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        self.query_api = self.client.query_api()
        self.write_api = self.client.write_api()
        self.bucket = INFLUXDB_BUCKET
        self.org = INFLUXDB_ORG

    def is_connected(self) -> bool:
        """Check if InfluxDB is reachable."""
        try:
            health = self.client.health()
            return health.status == "pass"
        except Exception:
            return False

    def get_sensor_history(
        self,
        tenant_id: str,
        sensor_type: str,
        range_str: str = "30d",
        location_id: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Fetch ANY sensor type's history for a specific tenant.
        Returns a DataFrame with columns: [ds, y, location_id].
        """
        location_filter = f'|> filter(fn: (r) => r.locationId == "{location_id}")' if location_id else ""

        flux = f'''
        from(bucket: "{self.bucket}")
            |> range(start: -{range_str})
            |> filter(fn: (r) => r._measurement == "{sensor_type}")
            |> filter(fn: (r) => r.tenantId == "{tenant_id}")
            {location_filter}
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
                        "y": float(record.get_value()),
                        "location_id": record.values.get("locationId", "default")
                    })

            if not records:
                logger.warning(f"No telemetry found for tenant={tenant_id}, sensor={sensor_type}")
                return pd.DataFrame(columns=["ds", "y", "location_id"])

            df = pd.DataFrame(records)
            df["ds"] = pd.to_datetime(df["ds"])
            df = df.sort_values("ds").reset_index(drop=True)
            return df

        except Exception as e:
            logger.error(f"InfluxDB query failed for tenant={tenant_id}, sensor={sensor_type}: {e}")
            return pd.DataFrame(columns=["ds", "y", "location_id"])

    def write_batch(
        self,
        tenant_id: str,
        sensor_type: str,
        df: pd.DataFrame,
        location_id: str = "default"
    ) -> int:
        """
        Batch write historical or uploaded CSV data to InfluxDB.
        Expects df to contain 'timestamp' (or 'ds') and 'value' (or 'y').
        """
        points = []
        ts_col = "timestamp" if "timestamp" in df.columns else ("ds" if "ds" in df.columns else None)
        val_col = "value" if "value" in df.columns else ("y" if "y" in df.columns else None)

        if not ts_col or not val_col:
            raise ValueError("DataFrame must contain timestamp/ds and value/y columns")

        for _, row in df.iterrows():
            ts = pd.to_datetime(row[ts_col])
            val = float(row[val_col])
            loc = str(row.get("locationId", row.get("location_id", location_id)))

            point = Point(sensor_type) \
                .tag("tenantId", tenant_id) \
                .tag("locationId", loc) \
                .field("value", val) \
                .time(ts, WritePrecision.NS)
            points.append(point)

        if points:
            self.write_api.write(bucket=self.bucket, org=self.org, record=points)
            logger.info(f"Wrote {len(points)} points to InfluxDB for tenant={tenant_id}, sensor={sensor_type}")

        return len(points)

    def get_weight_history(self, item_id: str, range_str: str = "30d") -> pd.DataFrame:
        """
        Legacy: Fetch weight history for a specific item.
        Returns a DataFrame with columns: [ds, y].
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
