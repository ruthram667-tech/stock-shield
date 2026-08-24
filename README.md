# 🛡️ Stock Shield

**IoT-powered smart inventory management system** — real-time stock monitoring with ML-driven forecasting, automated alerts, and a premium dark-mode dashboard.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: Edge & Hardware                                       │
│  ESP32 + HX711 (weight) + DHT22 (temp/humidity)                │
│  → JSON over MQTT                                               │
└──────────────────────┬──────────────────────────────────────────┘
                       │ MQTT (QoS 1)
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2: Backend & Data                                        │
│  Spring Boot 3.2 (Java 17)                                      │
│  ├─ MQTT Listener Thread → ConcurrentHashMap<ItemId, Status>    │
│  ├─ PostgreSQL: users, products, vendors, alerts (relational)   │
│  └─ InfluxDB: weight, temp, humidity time-series (telemetry)    │
└──────────────────────┬──────────────────────────────────────────┘
                       │ REST API
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3: ML Pipeline                                           │
│  FastAPI (Python 3.11)                                          │
│  ├─ Prophet (seasonal items) / ARIMA (stable demand)            │
│  ├─ Dynamic reorder point: ROP = (D × LT) + Z × σ × √LT       │
│  └─ Scheduled retrain every 6h → pushes thresholds to backend  │
└─────────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 4: Presentation & Alerts                                 │
│  React 18 + Chart.js dashboard (Vite, dark glassmorphism UI)    │
│  Twilio SMS + SendGrid email on threshold breach                │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your credentials

# 2. Launch all services
docker-compose up -d

# 3. Access
#    Dashboard:  http://localhost:3000
#    Backend:    http://localhost:8080/api/dashboard/summary
#    ML Service: http://localhost:8000/health
#    InfluxDB:   http://localhost:8086
```

## MQTT Topic Structure

| Topic | Payload | QoS |
|:------|:--------|:---:|
| `stockshield/shelf/{id}/weight` | `{ "shelfId", "itemId", "value", "unit", "fullWeight", "ts" }` | 1 |
| `stockshield/shelf/{id}/environment` | `{ "shelfId", "zone", "temp", "humidity", "ts" }` | 1 |
| `stockshield/shelf/{id}/status` | `{ "shelfId", "battery", "rssi", "uptime_sec", "ts" }` | 0 |

## REST API

### Backend (port 8080)

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| GET | `/api/inventory` | All items with live status |
| GET | `/api/inventory/{id}` | Single item detail |
| GET | `/api/inventory/alerts` | Items below reorder point |
| GET | `/api/telemetry/{shelfId}?range=24h` | Weight time-series |
| GET | `/api/telemetry/environment/{shelfId}` | Temp/humidity history |
| POST | `/api/thresholds/update` | ML pushes new reorder points |
| GET | `/api/thresholds` | Current thresholds |
| GET | `/api/dashboard/summary` | Aggregated dashboard stats |
| GET | `/api/dashboard/alerts/recent?limit=20` | Recent alerts |

### ML Service (port 8000)

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| POST | `/predict/{item_id}` | On-demand forecast |
| POST | `/predict/batch` | Batch forecast |
| GET | `/models/{item_id}/metrics` | Model accuracy (MAE, RMSE) |
| GET | `/health` | Service health check |

## Project Structure

```
stock-shield/
├── docker-compose.yml          # Full stack orchestration
├── .env.example                # Environment template
├── infra/mosquitto/            # MQTT broker config
├── edge-simulator/             # Python ESP32 simulator
│   ├── simulator.py
│   ├── config.json
│   └── Dockerfile
├── backend/                    # Spring Boot Java service
│   ├── pom.xml
│   ├── Dockerfile
│   └── src/main/
│       ├── java/com/stockshield/
│       │   ├── model/          # JPA entities + enums
│       │   ├── dto/            # API data transfer objects
│       │   ├── repository/     # JPA + InfluxDB repositories
│       │   ├── service/        # MQTT, Inventory, Alert, Threshold
│       │   ├── controller/     # REST endpoints
│       │   └── config/         # MQTT, InfluxDB, WebSocket, CORS
│       └── resources/
│           ├── application.yml
│           └── db/migration/   # Flyway SQL migrations
├── ml-service/                 # Python FastAPI ML pipeline
│   ├── app/
│   │   ├── main.py             # FastAPI endpoints
│   │   ├── forecaster.py       # Prophet/ARIMA models
│   │   ├── influx_client.py    # InfluxDB query wrapper
│   │   ├── scheduler.py        # Periodic retrain cron
│   │   └── models.py           # Pydantic schemas
│   ├── requirements.txt
│   └── Dockerfile
├── dashboard/                  # React + Chart.js frontend
│   ├── src/
│   │   ├── components/         # Sidebar, Navbar, Gauge, Chart
│   │   ├── pages/              # Dashboard, Inventory, Environment, Alerts
│   │   ├── api.js              # API client
│   │   ├── App.jsx
│   │   └── index.css           # Full design system
│   ├── package.json
│   ├── nginx.conf
│   └── Dockerfile
└── firmware/                   # ESP32 reference (not compiled)
    ├── stock_shield.ino
    └── platformio.ini
```

## Key Design Decisions

- **MQTT decouples hardware from backend** — lightweight, async, survives network issues
- **PostgreSQL + InfluxDB split** — relational integrity for business data, columnar time-series for telemetry
- **ML as a separate Python service** — swap Prophet/ARIMA freely without touching Java
- **ConcurrentHashMap for O(1) lookups** — live sensor state is always available without DB queries
- **WebSocket for real-time push** — dashboard updates without polling

## Tech Stack

| Layer | Technology |
|:------|:-----------|
| Edge | ESP32, HX711, DHT22, Arduino/PlatformIO |
| Broker | Mosquitto MQTT 2.x |
| Backend | Spring Boot 3.2, Java 17, Paho MQTT |
| Relational DB | PostgreSQL 16 + Flyway |
| Time-Series DB | InfluxDB 2.7 |
| ML | Python 3.11, FastAPI, Prophet, pmdarima |
| Frontend | React 18, Vite 5, Chart.js 4 |
| Alerts | Twilio (SMS), SendGrid (Email) |
| DevOps | Docker Compose |
