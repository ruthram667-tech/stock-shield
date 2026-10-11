"""
Stock Shield — Universal Multi-Tenant Edge Simulator
Simulates realistic IoT telemetry for any industry (Pharma, Chemical, Food, Agriculture, Retail).
Publishes to both generic (stockshield/{tenantId}/{locationId}/{sensorType}) and legacy MQTT topics.
"""

import json
import math
import os
import random
import signal
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Any

import paho.mqtt.client as mqtt

# ─── Configuration ───────────────────────────────────────────────────────────

MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
INTERVAL = int(os.getenv("SIMULATOR_INTERVAL_SEC", "5"))
CONFIG_PATH = os.getenv("SIMULATOR_CONFIG", os.path.join(os.path.dirname(__file__), "config.json"))

running = True


def signal_handler(sig, frame):
    global running
    print("\n⏹ Simulator shutting down...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ─── Generic Dynamic Sensor Simulator ─────────────────────────────────────────

class GenericSensorSimulator:
    """Simulates an individual sensor of any physical metric."""

    def __init__(self, tenant_id: str, location_id: str, sensor_cfg: dict, item_id: str = None):
        self.tenant_id = tenant_id
        self.location_id = location_id
        self.sensor_type = sensor_cfg["type"]
        self.unit = sensor_cfg.get("unit", "")
        self.target = float(sensor_cfg.get("target", 20.0))
        self.noise = float(sensor_cfg.get("noise", 0.1))
        self.drift = float(sensor_cfg.get("drift", 0.0))
        self.spike_prob = float(sensor_cfg.get("spike_prob", 0.005))
        self.spike_mag = float(sensor_cfg.get("spike_mag", 5.0))
        self.is_depleting = bool(sensor_cfg.get("is_depleting", False))
        self.depletion_rate = float(sensor_cfg.get("depletion_rate", 0.1))
        self.item_id = item_id

        # Initial value
        if self.is_depleting:
            self.current_value = self.target * random.uniform(0.65, 1.0)
            self.full_weight = self.target
        else:
            self.current_value = self.target + random.gauss(0, self.noise)
            self.full_weight = None

        self._time_offset = random.uniform(0, 100)
        self._restock_cooldown = 0

    def tick(self, dt_seconds: float):
        dt_hours = dt_seconds / 3600.0

        if self.is_depleting:
            # Weight/stock depletion
            noise = random.gauss(0, self.depletion_rate * 0.1)
            consumed = (self.depletion_rate + noise) * dt_hours
            if random.random() < 0.02:
                consumed += random.uniform(0.3, 1.0)  # burst batch pick
            self.current_value = max(0.0, self.current_value - consumed)

            # Auto-restock if low
            if self._restock_cooldown > 0:
                self._restock_cooldown -= 1
            elif self.current_value < self.full_weight * 0.15 and random.random() < 0.25:
                self.current_value = self.full_weight * random.uniform(0.85, 1.0)
                self._restock_cooldown = 12
                print(f"  📦 [Restocked] {self.location_id} {self.sensor_type} → {self.current_value:.2f}{self.unit}")

        else:
            # Physical metric (temperature, pressure, pH, vibration, etc.)
            # Periodic wave (e.g. ambient diurnal cycle)
            self._time_offset += dt_seconds / 60.0
            wave = 0.5 * math.sin(2 * math.pi * (self._time_offset / 1440.0))

            # Noise + Mean reversion to target + drift
            self.current_value += random.gauss(0, self.noise) + (wave * 0.02)
            self.current_value += (self.target - self.current_value) * 0.02

            # Occasional anomaly / spike
            if random.random() < self.spike_prob:
                spike = random.uniform(self.spike_mag * 0.5, self.spike_mag)
                direction = random.choice([1, -1]) if "ph" in self.sensor_type else 1
                self.current_value += (direction * spike)
                print(f"  ⚡ [{self.tenant_id}] SPIKE on {self.location_id}/{self.sensor_type}: {self.current_value:.2f} {self.unit}")

    def payload(self) -> dict:
        p = {
            "tenantId": self.tenant_id,
            "locationId": self.location_id,
            "sensorType": self.sensor_type,
            "value": round(self.current_value, 3),
            "unit": self.unit,
            "ts": datetime.now(timezone.utc).isoformat()
        }
        if self.item_id:
            p["itemId"] = self.item_id
        if self.full_weight:
            p["fullWeight"] = self.full_weight
        return p


# ─── Location Simulator ───────────────────────────────────────────────────────

class LocationSimulator:
    def __init__(self, tenant_id: str, loc_cfg: dict):
        self.tenant_id = tenant_id
        self.location_id = loc_cfg["location_id"]
        self.zone = loc_cfg.get("zone", "general")
        self.item_id = loc_cfg.get("item_id")
        self.item_name = loc_cfg.get("item_name")
        self.battery = random.randint(75, 100)
        self.rssi = random.randint(-65, -35)

        self.sensors: List[GenericSensorSimulator] = []
        for s_cfg in loc_cfg.get("sensors", []):
            self.sensors.append(GenericSensorSimulator(tenant_id, self.location_id, s_cfg, self.item_id))

    def tick(self, dt_seconds: float):
        for s in self.sensors:
            s.tick(dt_seconds)
        if random.random() < 0.01:
            self.battery = max(0, self.battery - 1)
        self.rssi = max(-85, min(-25, self.rssi + random.randint(-2, 2)))

    def status_payload(self) -> dict:
        return {
            "tenantId": self.tenant_id,
            "shelfId": self.location_id,
            "locationId": self.location_id,
            "battery": self.battery,
            "rssi": self.rssi,
            "ts": datetime.now(timezone.utc).isoformat()
        }


# ─── Main Simulator Engine ────────────────────────────────────────────────────

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"✅ Connected to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
    else:
        print(f"❌ MQTT connection failed (code {rc})")


def on_disconnect(client, userdata, rc, properties=None, reasonCode=None):
    print(f"⚠️ Disconnected from MQTT (rc={rc}), reconnecting...")


def main():
    config_path = CONFIG_PATH
    if not os.path.exists(config_path):
        config_path = os.path.join(os.path.dirname(__file__), "config.json")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Initialize locations across configured tenants
    active_tenants = config.get("active_tenants", ["demo-tenant"])
    locations: List[LocationSimulator] = []

    for tenant in config.get("tenants", []):
        t_id = tenant["tenant_id"]
        if t_id in active_tenants:
            for loc_cfg in tenant.get("locations", []):
                locations.append(LocationSimulator(t_id, loc_cfg))

    total_sensors = sum(len(l.sensors) for l in locations)
    print("=" * 60)
    print("🌐 Stock Shield — Universal Multi-Tenant Edge Simulator")
    print(f"   Active Tenants: {', '.join(active_tenants)}")
    print(f"   Locations:      {len(locations)}")
    print(f"   Total Sensors:  {total_sensors}")
    print(f"   Interval:       {INTERVAL}s")
    print(f"   Broker:         {MQTT_HOST}:{MQTT_PORT}")
    print("=" * 60)

    client = mqtt.Client(
        client_id=f"ss-universal-sim-{random.randint(1000, 9999)}",
        protocol=mqtt.MQTTv5
    )
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    try:
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    except Exception as e:
        print(f"❌ Failed to connect to MQTT broker: {e}")
        sys.exit(1)

    client.loop_start()
    tick_count = 0

    try:
        while running:
            tick_count += 1

            for loc in locations:
                loc.tick(INTERVAL)

                # Publish each dynamic sensor on generic topic:
                # stockshield/{tenantId}/{locationId}/{sensorType}
                for sensor in loc.sensors:
                    generic_topic = f"stockshield/{sensor.tenant_id}/{sensor.location_id}/{sensor.sensor_type}"
                    payload_data = sensor.payload()
                    client.publish(generic_topic, json.dumps(payload_data), qos=1)

                    # Also publish legacy topics if applicable for demo-tenant
                    if sensor.tenant_id == "demo-tenant":
                        if sensor.sensor_type == "weight":
                            legacy_topic = f"stockshield/shelf/{sensor.location_id}/weight"
                            client.publish(legacy_topic, json.dumps({
                                "shelfId": sensor.location_id,
                                "itemId": sensor.item_id,
                                "value": payload_data["value"],
                                "unit": sensor.unit,
                                "fullWeight": sensor.full_weight,
                                "ts": payload_data["ts"]
                            }), qos=1)

                # Periodic device status
                if tick_count % 12 == 0:
                    status_topic = f"stockshield/shelf/{loc.location_id}/status"
                    client.publish(status_topic, json.dumps(loc.status_payload()), qos=0)

            if tick_count % 6 == 0:
                print(f"📡 Tick {tick_count} | Published {total_sensors} sensors across {len(locations)} locations.")

            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()
        print("✅ Simulator shut down cleanly.")


if __name__ == "__main__":
    main()
