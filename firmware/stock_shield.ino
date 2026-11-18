/*
 * Stock Shield - ESP32 firmware (HTTP ingest)
 *
 * Hardware: ESP32 DevKit, DHT22 module, 0.96" SSD1306 I2C OLED,
 *           optional HX711 + load cell (set ENABLE_WEIGHT 1 once you have an HX711).
 *
 * Posts readings to the backend:  POST http://<PC_IP>:8080/api/ingest
 * See firmware/WIRING.md for connections.
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <DHT.h>

// 1 = read weight via HX711, 0 = skip (no HX711 yet)
#define ENABLE_WEIGHT 0
#if ENABLE_WEIGHT
#include <HX711.h>
#endif

// ─── Configuration (EDIT THESE) ─────────────────────────────────
const char* WIFI_SSID     = "YOUR_WIFI_SSID";       // must be 2.4 GHz
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* BACKEND_URL   = "http://192.168.1.100:8080/api/ingest"; // your PC's LAN IP

const char* TENANT_ID = "demo-tenant";
const char* SHELF_ID  = "shelf-01";
const char* ITEM_ID   = "item-001";

// ─── Pins ───────────────────────────────────────────────────────
#define DHT_PIN      27      // DHT22 "out"
#define DHT_TYPE     DHT22
#define OLED_SDA     21
#define OLED_SCL     22
#define OLED_ADDR    0x3C    // try 0x3D if the screen stays blank
#define HX711_DT     16
#define HX711_SCK    17

#define SEND_INTERVAL_MS 5000
#define HX711_SCALE_FACTOR 420.0   // calibrate with a known weight

// ─── Globals ────────────────────────────────────────────────────
Adafruit_SSD1306 oled(128, 64, &Wire, -1);
DHT dht(DHT_PIN, DHT_TYPE);
#if ENABLE_WEIGHT
HX711 scale;
#endif
bool oledOk = false;
unsigned long lastSend = 0;
int lastHttp = 0;

void connectWiFi() {
    if (WiFi.status() == WL_CONNECTED) return;
    Serial.printf("WiFi: connecting to %s", WIFI_SSID);
    WiFi.disconnect(true);   // clear any half-finished attempt before retrying
    delay(100);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start < 15000) {
        delay(500);
        Serial.print(".");
    }
    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("\nWiFi OK, IP %s\n", WiFi.localIP().toString().c_str());
    } else {
        Serial.println("\nWiFi failed, will retry");
    }
}

void drawScreen(float t, float h, float w, bool haveEnv) {
    if (!oledOk) return;
    oled.clearDisplay();
    oled.setTextColor(SSD1306_WHITE);
    oled.setTextSize(1);
    oled.setCursor(0, 0);
    oled.printf("STOCK SHIELD  %s", WiFi.status() == WL_CONNECTED ? "WiFi" : "----");
    oled.setCursor(0, 12);
    oled.printf("%s / %s", TENANT_ID, SHELF_ID);
    oled.setTextSize(2);
    oled.setCursor(0, 26);
    if (haveEnv) oled.printf("%.1fC %.0f%%", t, h);
    else oled.print("DHT error");
    oled.setTextSize(1);
    oled.setCursor(0, 48);
#if ENABLE_WEIGHT
    oled.printf("Weight: %.2f kg", w);
#else
    oled.print("Weight: n/a");
#endif
    oled.setCursor(0, 56);
    oled.printf("Server: %s", lastHttp == 200 ? "OK" : (lastHttp == 0 ? "-" : String(lastHttp).c_str()));
    oled.display();
}

bool postReadings(float t, float h, float w, bool haveEnv) {
    if (WiFi.status() != WL_CONNECTED) return false;

    JsonDocument doc;
    doc["tenantId"] = TENANT_ID;
    doc["locationId"] = SHELF_ID;
    doc["itemId"] = ITEM_ID;
    JsonArray readings = doc["readings"].to<JsonArray>();
    if (haveEnv) {
        JsonObject a = readings.add<JsonObject>();
        a["sensorType"] = "temperature";
        a["value"] = round(t * 100.0) / 100.0;
        JsonObject b = readings.add<JsonObject>();
        b["sensorType"] = "humidity";
        b["value"] = round(h * 100.0) / 100.0;
    }
#if ENABLE_WEIGHT
    JsonObject c = readings.add<JsonObject>();
    c["sensorType"] = "weight";
    c["value"] = round(w * 1000.0) / 1000.0;
#endif
    if (readings.size() == 0) return false;

    String body;
    serializeJson(doc, body);

    HTTPClient http;
    http.begin(BACKEND_URL);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(5000);
    lastHttp = http.POST(body);
    http.end();
    Serial.printf("POST %s -> %d  %s\n", BACKEND_URL, lastHttp, body.c_str());
    return lastHttp == 200;
}

void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.println("\nStock Shield ESP32 starting");

    Wire.begin(OLED_SDA, OLED_SCL);
    oledOk = oled.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR);
    Serial.println(oledOk ? "OLED OK" : "OLED not found (check wiring/address)");
    if (oledOk) {
        oled.clearDisplay();
        oled.setTextColor(SSD1306_WHITE);
        oled.setCursor(0, 0);
        oled.println("Stock Shield");
        oled.println("Starting...");
        oled.display();
    }

    dht.begin();

#if ENABLE_WEIGHT
    scale.begin(HX711_DT, HX711_SCK);
    scale.set_scale(HX711_SCALE_FACTOR);
    scale.tare();
#endif

    connectWiFi();
}

void loop() {
    connectWiFi();

    if (millis() - lastSend >= SEND_INTERVAL_MS) {
        lastSend = millis();

        float t = dht.readTemperature();
        float h = dht.readHumidity();
        bool haveEnv = !isnan(t) && !isnan(h);

        float w = 0;
#if ENABLE_WEIGHT
        if (scale.is_ready()) {
            w = scale.get_units(5);
            if (w < 0) w = 0;
        }
#endif
        postReadings(t, h, w, haveEnv);
        drawScreen(t, h, w, haveEnv);
    }
    delay(50);
}
