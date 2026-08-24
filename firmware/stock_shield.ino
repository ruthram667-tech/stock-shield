/*
 * ══════════════════════════════════════════════════════════════
 * Stock Shield — ESP32 Firmware (Reference Implementation)
 * ══════════════════════════════════════════════════════════════
 *
 * Hardware:
 *   - ESP32 DevKit V1 (or compatible)
 *   - HX711 ADC + Load Cell (weight sensing under shelf)
 *   - DHT22 (AM2302) temperature/humidity sensor
 *
 * Protocol: MQTT (QoS 1) → Mosquitto broker
 * Power: USB or LiPo with deep sleep between readings
 *
 * NOTE: This is a REFERENCE sketch — not compiled in this repo.
 *       Flash to ESP32 using PlatformIO or Arduino IDE.
 * ══════════════════════════════════════════════════════════════
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <HX711.h>
#include <DHT.h>
#include <time.h>

// ─── Configuration ──────────────────────────────────────────────

// Wi-Fi
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD  = "YOUR_WIFI_PASSWORD";

// MQTT
const char* MQTT_BROKER   = "192.168.1.100";  // Mosquitto IP
const int   MQTT_PORT     = 1883;
const char* MQTT_CLIENT   = "ss-esp32-shelf-01";

// Shelf identity
const char* SHELF_ID      = "shelf-01";
const char* ITEM_ID       = "item-001";

// Sensor pins
#define HX711_DOUT_PIN    4
#define HX711_SCK_PIN     5
#define DHT_PIN           15
#define DHT_TYPE          DHT22

// Timing
#define READ_INTERVAL_MS  5000   // 5 seconds between readings
#define STATUS_INTERVAL   12     // Send status every 12th reading
#define DEEP_SLEEP_US     5000000 // 5s deep sleep (optional)

// Calibration
#define HX711_SCALE_FACTOR  420.0  // Calibrate with known weight!
#define HX711_OFFSET        0

// ─── Globals ────────────────────────────────────────────────────

WiFiClient   espClient;
PubSubClient mqttClient(espClient);
HX711        scale;
DHT          dht(DHT_PIN, DHT_TYPE);

char topicWeight[80];
char topicEnv[80];
char topicStatus[80];
int  tickCount = 0;

// ─── Setup ──────────────────────────────────────────────────────

void setup() {
    Serial.begin(115200);
    Serial.println("\n🛡️ Stock Shield ESP32 starting...");

    // Build MQTT topics
    snprintf(topicWeight, sizeof(topicWeight), "stockshield/shelf/%s/weight", SHELF_ID);
    snprintf(topicEnv,    sizeof(topicEnv),    "stockshield/shelf/%s/environment", SHELF_ID);
    snprintf(topicStatus, sizeof(topicStatus), "stockshield/shelf/%s/status", SHELF_ID);

    // Initialize sensors
    scale.begin(HX711_DOUT_PIN, HX711_SCK_PIN);
    scale.set_scale(HX711_SCALE_FACTOR);
    scale.set_offset(HX711_OFFSET);
    scale.tare(); // Zero on startup
    Serial.println("✅ HX711 initialized");

    dht.begin();
    Serial.println("✅ DHT22 initialized");

    // Connect Wi-Fi
    connectWiFi();

    // Connect MQTT
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    connectMQTT();

    // Configure NTP for timestamps
    configTime(0, 0, "pool.ntp.org");
}

// ─── Main Loop ──────────────────────────────────────────────────

void loop() {
    if (!mqttClient.connected()) {
        connectMQTT();
    }
    mqttClient.loop();

    tickCount++;

    // ── Read weight ──
    float weightKg = 0;
    if (scale.is_ready()) {
        weightKg = scale.get_units(5);  // Average of 5 readings
        if (weightKg < 0) weightKg = 0; // Floor at 0
    }

    // ── Read temperature/humidity ──
    float tempC     = dht.readTemperature();
    float humidity   = dht.readHumidity();

    // ── Get ISO 8601 timestamp ──
    char timestamp[30];
    getISOTimestamp(timestamp, sizeof(timestamp));

    // ── Publish weight ──
    {
        JsonDocument doc;
        doc["shelfId"]    = SHELF_ID;
        doc["itemId"]     = ITEM_ID;
        doc["value"]      = round(weightKg * 1000.0) / 1000.0;
        doc["unit"]       = "kg";
        doc["fullWeight"]  = 25.0;  // Configure per shelf
        doc["ts"]         = timestamp;

        char payload[256];
        serializeJson(doc, payload);
        mqttClient.publish(topicWeight, payload, true);
    }

    // ── Publish environment ──
    if (!isnan(tempC) && !isnan(humidity)) {
        JsonDocument doc;
        doc["shelfId"]   = SHELF_ID;
        doc["zone"]      = "dry-storage";
        doc["temp"]      = round(tempC * 100.0) / 100.0;
        doc["humidity"]  = round(humidity * 100.0) / 100.0;
        doc["ts"]        = timestamp;

        char payload[256];
        serializeJson(doc, payload);
        mqttClient.publish(topicEnv, payload, true);
    }

    // ── Publish device status (every 12th tick) ──
    if (tickCount % STATUS_INTERVAL == 0) {
        JsonDocument doc;
        doc["shelfId"]     = SHELF_ID;
        doc["battery"]     = getBatteryPercent();
        doc["rssi"]        = WiFi.RSSI();
        doc["uptime_sec"]  = millis() / 1000;
        doc["ts"]          = timestamp;

        char payload[256];
        serializeJson(doc, payload);
        mqttClient.publish(topicStatus, payload);
    }

    // ── Log to serial ──
    Serial.printf("📡 [%s] W: %.2f kg | T: %.1f°C | H: %.1f%% | RSSI: %d dBm\n",
                  SHELF_ID, weightKg, tempC, humidity, WiFi.RSSI());

    delay(READ_INTERVAL_MS);
}

// ─── Helpers ────────────────────────────────────────────────────

void connectWiFi() {
    Serial.printf("📶 Connecting to %s", WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.printf("\n✅ WiFi connected — IP: %s\n", WiFi.localIP().toString().c_str());
}

void connectMQTT() {
    while (!mqttClient.connected()) {
        Serial.printf("📡 Connecting to MQTT broker at %s:%d...\n", MQTT_BROKER, MQTT_PORT);
        if (mqttClient.connect(MQTT_CLIENT)) {
            Serial.println("✅ MQTT connected");
        } else {
            Serial.printf("❌ MQTT failed (rc=%d), retrying in 5s...\n", mqttClient.state());
            delay(5000);
        }
    }
}

void getISOTimestamp(char* buffer, size_t len) {
    struct tm timeinfo;
    if (getLocalTime(&timeinfo)) {
        strftime(buffer, len, "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
    } else {
        snprintf(buffer, len, "1970-01-01T00:00:00Z");
    }
}

int getBatteryPercent() {
    // Read ADC on battery voltage divider pin (GPIO 34 typically)
    // This is a simplified version — real implementation needs calibration
    int raw = analogRead(34);
    float voltage = raw * (3.3 / 4095.0) * 2; // Assuming 1:1 voltage divider
    int percent = (int)((voltage - 3.0) / (4.2 - 3.0) * 100);
    return constrain(percent, 0, 100);
}
