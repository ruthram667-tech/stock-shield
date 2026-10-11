"""
Stock Shield — Model Storage & Persistence
Stores trained models and metadata per tenant and sensor type on disk.
Directory structure: models/{tenant_id}/{sensor_type}/
"""

import os
import json
import pickle
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

MODELS_DIR = os.getenv("MODELS_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "models"))


class ModelStore:
    def __init__(self, base_dir: str = MODELS_DIR):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_path(self, tenant_id: str, sensor_type: str) -> str:
        tenant_clean = "".join(c for c in tenant_id if c.isalnum() or c in ("-", "_"))
        sensor_clean = "".join(c for c in sensor_type if c.isalnum() or c in ("-", "_"))
        path = os.path.join(self.base_dir, tenant_clean, sensor_clean)
        os.makedirs(path, exist_ok=True)
        return path

    def save_model(
        self,
        tenant_id: str,
        sensor_type: str,
        model_artifact: Any,
        metadata: Dict[str, Any],
        thresholds: Dict[str, Any]
    ):
        """Save trained model object, metadata, and learned thresholds."""
        dir_path = self._get_path(tenant_id, sensor_type)

        model_file = os.path.join(dir_path, "model.pkl")
        meta_file = os.path.join(dir_path, "metadata.json")
        thresh_file = os.path.join(dir_path, "thresholds.json")

        try:
            with open(model_file, "wb") as f:
                pickle.dump(model_artifact, f)

            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, default=str)

            with open(thresh_file, "w", encoding="utf-8") as f:
                json.dump(thresholds, f, indent=2, default=str)

            logger.info(f"💾 Successfully saved model and metadata for {tenant_id}/{sensor_type}")
        except Exception as e:
            logger.error(f"Failed to persist model for {tenant_id}/{sensor_type}: {e}")
            raise

    def load_model(self, tenant_id: str, sensor_type: str) -> Optional[Any]:
        """Load pickled model object."""
        dir_path = self._get_path(tenant_id, sensor_type)
        model_file = os.path.join(dir_path, "model.pkl")
        if not os.path.exists(model_file):
            return None
        try:
            with open(model_file, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Failed to load model for {tenant_id}/{sensor_type}: {e}")
            return None

    def get_metadata(self, tenant_id: str, sensor_type: str) -> Optional[Dict[str, Any]]:
        dir_path = self._get_path(tenant_id, sensor_type)
        meta_file = os.path.join(dir_path, "metadata.json")
        if not os.path.exists(meta_file):
            return None
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read metadata for {tenant_id}/{sensor_type}: {e}")
            return None

    def get_thresholds(self, tenant_id: str, sensor_type: str) -> Optional[Dict[str, Any]]:
        dir_path = self._get_path(tenant_id, sensor_type)
        thresh_file = os.path.join(dir_path, "thresholds.json")
        if not os.path.exists(thresh_file):
            return None
        try:
            with open(thresh_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read thresholds for {tenant_id}/{sensor_type}: {e}")
            return None

    def list_models_for_tenant(self, tenant_id: str) -> List[Dict[str, Any]]:
        tenant_clean = "".join(c for c in tenant_id if c.isalnum() or c in ("-", "_"))
        tenant_dir = os.path.join(self.base_dir, tenant_clean)
        if not os.path.exists(tenant_dir):
            return []

        results = []
        for sensor_type in os.listdir(tenant_dir):
            sensor_dir = os.path.join(tenant_dir, sensor_type)
            if os.path.isdir(sensor_dir):
                meta = self.get_metadata(tenant_id, sensor_type)
                thresh = self.get_thresholds(tenant_id, sensor_type)
                if meta:
                    meta["learned_thresholds"] = thresh
                    results.append(meta)
        return results

    def list_all_models(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.base_dir):
            return []
        all_models = []
        for tenant_id in os.listdir(self.base_dir):
            tenant_path = os.path.join(self.base_dir, tenant_id)
            if os.path.isdir(tenant_path):
                all_models.extend(self.list_models_for_tenant(tenant_id))
        return all_models


# Global instance
model_store = ModelStore()
