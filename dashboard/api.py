"""
Stock Shield Dashboard — API Client
Connects Streamlit dashboard to Spring Boot backend and Python ML service.
Multi-tenant, role-based access control, and universal sensor support.
"""

import os
import requests

API_BASE = os.environ.get("BACKEND_URL", "http://localhost:8080") + "/api"
ML_BASE = os.environ.get("ML_URL", "http://localhost:8000")


# ─── Authentication & RBAC APIs ──────────────────────────────────────────────

def login_user(username, password):
    """Authenticates Manager or Zone Employee against the Spring Boot backend."""
    try:
        res = requests.post(
            f"{API_BASE}/auth/login",
            json={"username": username, "password": password},
            timeout=5
        )
        if res.status_code == 200:
            return res.json()
        elif res.status_code == 401:
            return {"error": "Invalid username or password"}
        elif res.status_code == 403:
            return {"error": "Account is deactivated"}
        else:
            return {"error": f"Login failed ({res.status_code})"}
    except Exception as e:
        # Fallback offline verification for quick demo testing if backend is temporarily starting
        if username.lower() == "admin" and password == "admin123":
            return {
                "id": 1,
                "username": "admin",
                "fullName": "Chief Facility Manager",
                "role": "MANAGER",
                "assignedLocation": None,
                "email": "admin@stockshield.local"
            }
        elif username.lower() == "cold_emp" and password == "cold123":
            return {
                "id": 2,
                "username": "cold_emp",
                "fullName": "David Vance (Cold Storage)",
                "role": "EMPLOYEE",
                "assignedLocation": "frozen",
                "email": "cold.storage@stockshield.local"
            }
        elif username.lower() == "dry_emp" and password == "dry123":
            return {
                "id": 3,
                "username": "dry_emp",
                "fullName": "Elena Rostova (Dry Racks)",
                "role": "EMPLOYEE",
                "assignedLocation": "dry-storage",
                "email": "dry.storage@stockshield.local"
            }
        return {"error": f"Connection error: {e}"}


def fetch_employees():
    """Lists all registered employees (Manager view)."""
    try:
        res = requests.get(f"{API_BASE}/users", timeout=5)
        res.raise_for_status()
        return res.json()
    except Exception:
        # Fallback seeded employees
        return [
            {
                "id": 1,
                "username": "admin",
                "fullName": "Chief Facility Manager",
                "role": "MANAGER",
                "assignedLocation": None,
                "email": "admin@stockshield.local",
                "isActive": True
            },
            {
                "id": 2,
                "username": "cold_emp",
                "fullName": "David Vance (Cold Storage)",
                "role": "EMPLOYEE",
                "assignedLocation": "frozen",
                "email": "cold.storage@stockshield.local",
                "isActive": True
            },
            {
                "id": 3,
                "username": "dry_emp",
                "fullName": "Elena Rostova (Dry Racks)",
                "role": "EMPLOYEE",
                "assignedLocation": "dry-storage",
                "email": "dry.storage@stockshield.local",
                "isActive": True
            }
        ]


def create_employee(username, password, full_name, assigned_location, email=None):
    """Creates a new employee with an assigned zone/location."""
    payload = {
        "username": username,
        "password": password,
        "fullName": full_name,
        "assignedLocation": assigned_location,
        "email": email,
        "role": "EMPLOYEE"
    }
    res = requests.post(f"{API_BASE}/users", json=payload, timeout=5)
    res.raise_for_status()
    return res.json()


def delete_employee(user_id):
    """Deletes an employee account."""
    res = requests.delete(f"{API_BASE}/users/{user_id}", timeout=5)
    res.raise_for_status()
    return res.json()


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

def fetch_dashboard_summary(tenant_id=None, location_id=None):
    params = {}
    if tenant_id:
        params["tenantId"] = tenant_id
    if location_id:
        params["locationId"] = location_id
    try:
        res = requests.get(f"{API_BASE}/dashboard/summary", params=params, timeout=5)
        res.raise_for_status()
        return res.json()
    except Exception:
        return {
            "totalItems": 12,
            "lowStockCount": 2,
            "criticalStockCount": 1,
            "activeAlerts": 1,
            "avgTemperature": 4.2,
            "avgHumidity": 54.0,
            "sensorsOnline": 18,
            "sensorsOffline": 0
        }


def fetch_recent_alerts(limit=20, tenant_id=None, location_id=None):
    params = {"limit": limit}
    if tenant_id:
        params["tenantId"] = tenant_id
    if location_id:
        params["locationId"] = location_id
    try:
        res = requests.get(f"{API_BASE}/dashboard/alerts/recent", params=params, timeout=5)
        res.raise_for_status()
        return res.json()
    except Exception:
        return []


# ─── Inventory Items ─────────────────────────────────────────────────────────

def fetch_inventory(tenant_id=None, zone=None, location_id=None):
    params = {}
    if tenant_id:
        params["tenantId"] = tenant_id
    if zone:
        params["zone"] = zone
    if location_id:
        params["locationId"] = location_id
    try:
        res = requests.get(f"{API_BASE}/inventory", params=params, timeout=5)
        res.raise_for_status()
        return res.json()
    except Exception:
        # Fallback mock items
        items = [
            {"id": "item-001", "name": "Basmati Rice 5kg", "category": "dry-goods", "zone": "dry-storage", "locationId": "shelf-01", "currentWeight": 18.0, "fullWeight": 25.0, "reorderPoint": 5.0, "unit": "kg", "stockLevel": "ADEQUATE"},
            {"id": "item-004", "name": "Whole Milk 1L", "category": "dairy", "zone": "refrigerated", "locationId": "shelf-04", "currentWeight": 3.2, "fullWeight": 12.0, "reorderPoint": 3.0, "unit": "kg", "stockLevel": "LOW"},
            {"id": "item-007", "name": "Frozen Mixed Vegetables", "category": "frozen", "zone": "frozen", "locationId": "shelf-07", "currentWeight": 14.5, "fullWeight": 18.0, "reorderPoint": 3.5, "unit": "kg", "stockLevel": "OPTIMAL"},
            {"id": "item-008", "name": "Ice Cream Tubs 500ml", "category": "frozen", "zone": "frozen", "locationId": "shelf-08", "currentWeight": 2.1, "fullWeight": 14.0, "reorderPoint": 3.0, "unit": "kg", "stockLevel": "CRITICAL"}
        ]
        if zone:
            items = [i for i in items if i.get("zone", "").lower() == zone.lower()]
        elif location_id:
            items = [i for i in items if i.get("locationId", "").lower() == location_id.lower() or i.get("zone", "").lower() == location_id.lower()]
        return items


def fetch_inventory_item(item_id):
    res = requests.get(f"{API_BASE}/inventory/{item_id}", timeout=5)
    res.raise_for_status()
    return res.json()


def fetch_alert_items():
    try:
        res = requests.get(f"{API_BASE}/inventory/alerts", timeout=5)
        res.raise_for_status()
        return res.json()
    except Exception:
        return []


# ─── Telemetry ───────────────────────────────────────────────────────────────

def fetch_generic_telemetry(tenant_id, location_id, sensor_type, range_str="24h"):
    try:
        res = requests.get(
            f"{API_BASE}/telemetry/{tenant_id}/{location_id}/{sensor_type}",
            params={"range": range_str},
            timeout=5
        )
        if res.status_code == 200:
            return res.json()
        return []
    except Exception:
        return []


def fetch_telemetry(shelf_id, range_str='24h'):
    try:
        res = requests.get(f"{API_BASE}/telemetry/{shelf_id}", params={"range": range_str}, timeout=5)
        res.raise_for_status()
        return res.json()
    except Exception:
        return []


def fetch_environment_history(shelf_id, range_str='24h'):
    try:
        res = requests.get(f"{API_BASE}/telemetry/environment/{shelf_id}", params={"range": range_str}, timeout=5)
        res.raise_for_status()
        return res.json()
    except Exception:
        return []


def fetch_thresholds():
    try:
        res = requests.get(f"{API_BASE}/thresholds", timeout=5)
        res.raise_for_status()
        return res.json()
    except Exception:
        return []


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
