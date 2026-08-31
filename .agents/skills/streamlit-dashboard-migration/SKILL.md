---
name: streamlit-dashboard-migration
description: Workflow and boilerplate for scaffolding a Streamlit dashboard, especially when migrating from an SPA (like React) or building a new dashboard.
---

# Streamlit Dashboard Migration / Implementation

When asked to build or migrate to a Streamlit dashboard that interacts with a backend API, follow these guidelines to ensure a robust and standard implementation.

## 1. Dependency Management
Create a `requirements.txt` file including the necessary libraries:
- `streamlit`
- `pandas`
- `requests`
- `plotly` (or other charting libraries)

## 2. API Layer
Isolate backend HTTP calls into an `api.py` module. Use environment variables for the backend URL.
Example:
```python
import os
import requests

API_BASE = os.environ.get("BACKEND_URL", "http://backend:8080") + "/api"

def fetch_data():
    res = requests.get(f"{API_BASE}/endpoint")
    res.raise_for_status()
    return res.json()
```

## 3. Application Structure
Use Streamlit's multipage app structure for dashboards with multiple views.
- Create a main `app.py` as the landing page (e.g., Dashboard Overview).
- Create a `pages/` directory for sub-pages (e.g., `pages/1_Inventory.py`, `pages/2_Alerts.py`).

## 4. Dockerization
Use a lightweight python image to containerize the application. Be sure to avoid vulnerable older slim images (e.g., use `python:3.12-slim`).
Example `Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## 5. Docker Compose Integration
When adding the dashboard to a `docker-compose.yml`, ensure the port `8501` is exposed and the `BACKEND_URL` is passed correctly to the container.
Example:
```yaml
  dashboard:
    build:
      context: ./dashboard
      dockerfile: Dockerfile
    ports:
      - "8501:8501"
    environment:
      BACKEND_URL: http://backend:8080
    depends_on:
      - backend
```
