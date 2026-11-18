# Stock Shield: wiring and setup

All power comes from the ESP32's 3V3 pin. Common ground everywhere. Use the board's labels (G21 = GPIO21).

## Connections

| Device pin | ESP32 pin | Notes |
|---|---|---|
| DHT22 **+** | 3V3 | |
| DHT22 **out** | **G27** | module has a built-in pull-up |
| DHT22 **-** | GND | |
| OLED **GND** | GND | |
| OLED **VCC/VDD** | 3V3 | |
| OLED **SCK** (SCL) | **G22** | |
| OLED **SDA** | **G21** | |

### Weight (only after you get an HX711)
Do **not** use the PAM8403. It is an audio amplifier and cannot read a load cell.

| Load cell wire | HX711 pin |
|---|---|
| Red | E+ |
| Black | E- |
| White | A- |
| Green | A+ |

(If the reading goes negative when you add weight, swap white and green.)

| HX711 pin | ESP32 pin |
|---|---|
| VCC | 3V3 |
| GND | GND |
| DT | G16 |
| SCK | G17 |

Then set `#define ENABLE_WEIGHT 1` in `stock_shield.ino`, and calibrate `HX711_SCALE_FACTOR` with a known weight.

## Software link

1. Start the stack: `docker compose up -d`
2. Find your PC's LAN IP (`ipconfig`, look for IPv4 on your Wi-Fi adapter).
3. Edit the top of `stock_shield.ino`: `WIFI_SSID`, `WIFI_PASSWORD`, and `BACKEND_URL` (`http://<PC_IP>:8080/api/ingest`).
4. Allow inbound TCP 8080 in Windows Firewall for the private network.
5. The ESP32 needs **2.4 GHz** Wi-Fi, on the same network as the PC.
6. Flash with PlatformIO (`pio run -t upload`) or Arduino IDE (board "ESP32 Dev Module", install the libraries in `platformio.ini`).
7. Open the serial monitor at 115200 baud. You should see `POST ... -> 200`.
8. The dashboard at http://localhost:8501 should show tenant `demo-tenant`, location `shelf-01`.

## Payload
```
POST /api/ingest
{"tenantId":"demo-tenant","locationId":"shelf-01","itemId":"item-001",
 "readings":[{"sensorType":"temperature","value":24.5},{"sensorType":"humidity","value":55.2}]}
```

## ESP32-CAM (separate device, live stream)
- AI-Thinker ESP32-CAM seated on its MB USB base. No wiring to the main ESP32.
- Make sure the camera ribbon is fully inserted and the latch is closed.
- Flash `firmware/esp32_cam/esp32_cam.ino` (board "AI Thinker ESP32-CAM"). Set `WIFI_SSID` / `WIFI_PASSWORD` first.
- If upload fails, hold BOOT on the MB base while it connects.
- The serial monitor (115200) prints `Stream: http://<ip>:81/stream`.
- Dashboard: open the **Camera** page and enter that IP.
- Power from a good USB port; weak supplies cause brown-outs and reboots.
