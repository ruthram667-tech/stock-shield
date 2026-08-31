import os
import requests

API_BASE = os.environ.get("BACKEND_URL", "http://backend:8080") + "/api"

def fetch_dashboard_summary():
    res = requests.get(f"{API_BASE}/dashboard/summary")
    res.raise_for_status()
    return res.json()

def fetch_inventory():
    res = requests.get(f"{API_BASE}/inventory")
    res.raise_for_status()
    return res.json()

def fetch_inventory_item(item_id):
    res = requests.get(f"{API_BASE}/inventory/{item_id}")
    res.raise_for_status()
    return res.json()

def fetch_alert_items():
    res = requests.get(f"{API_BASE}/inventory/alerts")
    res.raise_for_status()
    return res.json()

def fetch_recent_alerts(limit=20):
    res = requests.get(f"{API_BASE}/dashboard/alerts/recent", params={"limit": limit})
    res.raise_for_status()
    return res.json()

def fetch_telemetry(shelf_id, range_str='24h'):
    res = requests.get(f"{API_BASE}/telemetry/{shelf_id}", params={"range": range_str})
    res.raise_for_status()
    return res.json()

def fetch_environment_history(shelf_id, range_str='24h'):
    res = requests.get(f"{API_BASE}/telemetry/environment/{shelf_id}", params={"range": range_str})
    res.raise_for_status()
    return res.json()

def fetch_thresholds():
    res = requests.get(f"{API_BASE}/thresholds")
    res.raise_for_status()
    return res.json()
