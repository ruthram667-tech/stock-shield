"""
Stock Shield — Edge Simulator
Mimics ESP32 + HX711/DHT22 sensor readings and publishes to MQTT.
Generates realistic weight depletion curves and environmental fluctuations.
"""

import json
import math
import os
import random
import signal
import sys
import time
from datetime import datetime, timezone

import numpy as np
import paho.mqtt.client as mqtt

# ─── Configuration ───────────────────────────────────────────────────────────

MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
INTERVAL = int(os.getenv("SIMULATOR_INTERVAL_SEC", "5"))
CONFIG_PATH = os.getenv("SIMULATOR_CONFIG", "/app/config.json")

TOPIC_WEIGHT = "stockshield/shelf/{shelf_id}/weight"
TOPIC_ENV = "stockshield/shelf/{shelf_id}/environment"
TOPIC_STATUS = "stockshield/shelf/{shelf_id}/status"

running = True


def signal_handler(sig, frame):
    global running
    print("\n⏹  Simulator shutting down...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ─── Shelf State ─────────────────────────────────────────────────────────────

class ShelfSimulator:
    """Simulates a single shelf with weight depletion and environmental sensors."""

    def __init__(self, config: dict):
        self.shelf_id = config["shelf_id"]
        self.zone = config["zone"]
        self.product = config["product"]
        self.full_weight = config["product"]["full_weight_kg"]
        self.depletion_rate = config["depletion_rate_kg_per_hour"]
        self.temp_target = config["temp_target_c"]
        self.humidity_target = config["humidity_target_pct"]

        # Start at a random stock level (60-100%)
        self.current_weight = self.full_weight * random.uniform(0.6, 1.0)
        self.temp = self.temp_target + random.gauss(0, 0.3)
        self.humidity = self.humidity_target + random.gauss(0, 2.0)
        self.battery = random.randint(70, 100)
        self.rssi = random.randint(-65, -30)

        # Restock simulation: probability of restock when low
        self._restock_cooldown = 0

    def tick(self, dt_seconds: float):
        """Advance the simulation by dt_seconds."""
        dt_hours = dt_seconds / 3600.0

        # ── Weight depletion ──
        # Exponential decay with noise simulates real consumption
        noise = random.gauss(0, self.depletion_rate * 0.15)
        depletion = (self.depletion_rate + noise) * dt_hours

        # Add occasional "burst" consumption (someone grabs multiple items)
        if random.random() < 0.02:
            depletion += random.uniform(0.5, 2.0)

        self.current_weight = max(0.0, self.current_weight - depletion)

        # ── Auto-restock when near empty ──
        if self._restock_cooldown > 0:
            self._restock_cooldown -= 1
        elif self.current_weight < self.full_weight * 0.1 and random.random() < 0.3:
            self.current_weight = self.full_weight * random.uniform(0.85, 1.0)
            self._restock_cooldown = int(60 / max(dt_seconds, 1))  # cooldown ~60s
            print(f"  📦 Restocked {self.shelf_id} ({self.product['name']})")

        # ── Temperature (sinusoidal + random walk) ──
        hour_of_day = datetime.now().hour + datetime.now().minute / 60.0
        daily_wave = 0.5 * math.sin(2 * math.pi * (hour_of_day - 14) / 24)
        self.temp += random.gauss(0, 0.05) + daily_wave * 0.02
        # Mean-revert toward target
        self.temp += (self.temp_target - self.temp) * 0.01

        # Occasional temp spike (compressor issue, door left open)
        if random.random() < 0.005:
            spike = random.uniform(2.0, 6.0)
            self.temp += spike
            print(f"  🌡️  Temp spike on {self.shelf_id}: +{spike:.1f}°C")

        # ── Humidity (correlated with temp) ──
        self.humidity += random.gauss(0, 0.3)
        self.humidity += (self.humidity_target - self.humidity) * 0.02
        self.humidity = max(10.0, min(99.0, self.humidity))

        # ── Battery drain ──
        if random.random() < 0.01:
            self.battery = max(0, self.battery - 1)

        # ── Wi-Fi RSSI fluctuation ──
        self.rssi = max(-80, min(-20, self.rssi + random.randint(-2, 2)))

    def weight_payload(self) -> dict:
        return {
            "shelfId": self.shelf_id,
            "itemId": self.product["item_id"],
            "value": round(self.current_weight, 3),
            "unit": "kg",
            "fullWeight": self.full_weight,
            "ts": datetime.now(timezone.utc).isoformat()
        }

    def environment_payload(self) -> dict:
        return {
            "shelfId": self.shelf_id,
            "zone": self.zone,
            "temp": round(self.temp, 2),
            "humidity": round(self.humidity, 2),
            "ts": datetime.now(timezone.utc).isoformat()
        }

    def status_payload(self) -> dict:
        return {
            "shelfId": self.shelf_id,
            "battery": self.battery,
            "rssi": self.rssi,
            "uptime_sec": int(time.time()) % 86400,
            "ts": datetime.now(timezone.utc).isoformat()
        }


# ─── MQTT Callbacks ──────────────────────────────────────────────────────────

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"✅ Connected to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
    else:
        print(f"❌ MQTT connection failed with code {rc}")


def on_disconnect(client, userdata, rc, properties=None, reasonCode=None):
    print(f"⚠️  Disconnected from MQTT (rc={rc}), will auto-reconnect...")


# ─── Main Loop ───────────────────────────────────────────────────────────────

def main():
    # Load shelf configuration
    config_path = CONFIG_PATH
    if not os.path.exists(config_path):
        config_path = os.path.join(os.path.dirname(__file__), "config.json")

    with open(config_path, "r") as f:
        config = json.load(f)

    shelves = [ShelfSimulator(s) for s in config["shelves"]]
    print(f"🏭 Stock Shield Edge Simulator")
    print(f"   Shelves: {len(shelves)}")
    print(f"   Interval: {INTERVAL}s")
    print(f"   Broker: {MQTT_HOST}:{MQTT_PORT}")
    print()

    # Connect to MQTT
    client = mqtt.Client(
        client_id=f"ss-simulator-{random.randint(1000,9999)}",
        protocol=mqtt.MQTTv5
    )
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    try:
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    except Exception as e:
        print(f"❌ Cannot connect to MQTT broker: {e}")
        sys.exit(1)

    client.loop_start()
    tick_count = 0

    try:
        while running:
            tick_count += 1

            for shelf in shelves:
                shelf.tick(INTERVAL)

                # Publish weight every tick
                weight_topic = TOPIC_WEIGHT.format(shelf_id=shelf.shelf_id)
                weight_payload = json.dumps(shelf.weight_payload())
                client.publish(weight_topic, weight_payload, qos=1)

                # Publish environment every tick
                env_topic = TOPIC_ENV.format(shelf_id=shelf.shelf_id)
                env_payload = json.dumps(shelf.environment_payload())
                client.publish(env_topic, env_payload, qos=1)

                # Publish status every 12th tick (~60s at 5s interval)
                if tick_count % 12 == 0:
                    status_topic = TOPIC_STATUS.format(shelf_id=shelf.shelf_id)
                    status_payload = json.dumps(shelf.status_payload())
                    client.publish(status_topic, status_payload, qos=1)

            if tick_count % 6 == 0:  # Log summary every ~30s
                low = sum(1 for s in shelves if s.current_weight < s.full_weight * 0.2)
                print(
                    f"📡 Tick {tick_count} | "
                    f"Published {len(shelves)} shelves | "
                    f"Low stock: {low}/{len(shelves)}"
                )

            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()
        print("✅ Simulator stopped cleanly.")


if __name__ == "__main__":
    main()
