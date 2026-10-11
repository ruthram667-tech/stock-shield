"""
Stock Shield Dashboard — API Client
Connects Streamlit dashboard to Spring Boot backend and Python ML service.
Multi-tenant and universal sensor support.
"""

import os
import requests

API_BASE = os.environ.get("BACKEND_URL", "http://localhost:8080") + "/api"
ML_BASE = os.environ.get("ML_URL", "http://localhost:8000")


# ─── Tenant & Organization APIs ──────────────────────────────────────────────

def fetch_tenants():
    try:
        res = requests.get(f"{API_BASE}/tenants", timeout=5)
        res.raise_for_status()
        return res.json()
    except Exception:
        return [
            {"id": "demo-tenant", "name": "Global Retail Corp", "industry": "retail_grocery"},
            {"id": "pharma-corp", "name": "Apex BioPharma", "industry": "pharmaceutical"},
            {"id": "chem-corp", "name": "Vortex Chemical Solutions", "industry": "chemical_manufacturing"}
        ]


def create_tenant(name, industry):
    res = requests.post(f"{API_BASE}/tenants", json={"name": name, "industry": industry}, timeout=5)
    res.raise_for_status()
    return res.json()


# ─── Dynamic Sensor Type Registry ────────────────────────────────────────────

def fetch_sensor_types(tenant_id="demo-tenant"):
    try:
        res = requests.get(f"{API_BASE}/sensors/types", params={"tenantId": tenant_id}, timeout=5)
        res.raise_for_status()
        return res.json()
    except Exception:
        return []


def create_sensor_type(payload):
    res = requests.post(f"{API_BASE}/sensors/types", json=payload, timeout=5)
    res.raise_for_status()
    return res.json()


def update_sensor_type(sensor_id, payload):
    res = requests.put(f"{API_BASE}/sensors/types/{sensor_id}", json=payload, timeout=5)
    res.raise_for_status()
    return res.json()


# ─── Summary & Alerts ────────────────────────────────────────────────────────

def fetch_dashboard_summary(tenant_id=None):
    params = {}
    if tenant_id:
        params["tenantId"] = tenant_id
    res = requests.get(f"{API_BASE}/dashboard/summary", params=params, timeout=5)
    res.raise_for_status()
    return res.json()


def fetch_recent_alerts(limit=20, tenant_id=None):
    params = {"limit": limit}
    if tenant_id:
        params["tenantId"] = tenant_id
    res = requests.get(f"{API_BASE}/dashboard/alerts/recent", params=params, timeout=5)
    res.raise_for_status()
    return res.json()


# ─── Inventory Items ─────────────────────────────────────────────────────────

def fetch_inventory():
    res = requests.get(f"{API_BASE}/inventory", timeout=5)
    res.raise_for_status()
    return res.json()


def fetch_inventory_item(item_id):
    res = requests.get(f"{API_BASE}/inventory/{item_id}", timeout=5)
    res.raise_for_status()
    return res.json()


def fetch_alert_items():
    res = requests.get(f"{API_BASE}/inventory/alerts", timeout=5)
    res.raise_for_status()
    return res.json()


# ─── Telemetry ───────────────────────────────────────────────────────────────

def fetch_generic_telemetry(tenant_id, location_id, sensor_type, range_str="24h"):
    res = requests.get(
        f"{API_BASE}/telemetry/generic/{tenant_id}/{location_id}/{sensor_type}",
        params={"range": range_str},
        timeout=5
    )
    res.raise_for_status()
    return res.json()


def fetch_telemetry(shelf_id, range_str='24h'):
    res = requests.get(f"{API_BASE}/telemetry/{shelf_id}", params={"range": range_str}, timeout=5)
    res.raise_for_status()
    return res.json()


def fetch_environment_history(shelf_id, range_str='24h'):
    res = requests.get(f"{API_BASE}/telemetry/environment/{shelf_id}", params={"range": range_str}, timeout=5)
    res.raise_for_status()
    return res.json()


def fetch_thresholds():
    res = requests.get(f"{API_BASE}/thresholds", timeout=5)
    res.raise_for_status()
    return res.json()


# ─── Custom ML Model Training & Forecast APIs ────────────────────────────────

def train_custom_model(tenant_id, sensor_type, training_window="30d", service_level=0.95):
    res = requests.post(
        f"{ML_BASE}/train/{tenant_id}/{sensor_type}",
        json={"training_window": training_window, "service_level": service_level},
        timeout=30
    )
    res.raise_for_status()
    return res.json()


def predict_custom_model(tenant_id, sensor_type, horizon_hours=24, service_level=0.95):
    res = requests.post(
        f"{ML_BASE}/predict/{tenant_id}/{sensor_type}",
        json={"horizon_hours": horizon_hours, "service_level": service_level},
        timeout=15
    )
    res.raise_for_status()
    return res.json()


def upload_training_csv(tenant_id, sensor_type, file_bytes, filename="data.csv"):
    files = {"file": (filename, file_bytes, "text/csv")}
    res = requests.post(
        f"{ML_BASE}/upload/{tenant_id}/{sensor_type}",
        files=files,
        timeout=30
    )
    res.raise_for_status()
    return res.json()


def fetch_tenant_models(tenant_id):
    try:
        res = requests.get(f"{ML_BASE}/models/{tenant_id}", timeout=5)
        res.raise_for_status()
        return res.json()
    except Exception:
        return []
