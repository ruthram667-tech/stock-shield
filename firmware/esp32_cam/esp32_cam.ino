/*
 * Stock Shield - ESP32-CAM live MJPEG stream (AI-Thinker board)
 *
 * Separate device from the sensor node. Serves:
 *   http://<cam-ip>/          -> info page
 *   http://<cam-ip>:81/stream -> MJPEG live stream
 *   http://<cam-ip>/capture   -> single JPEG
 * Arduino IDE: board "AI Thinker ESP32-CAM", Partition "Huge APP" if prompted.
 */

#include <WiFi.h>
#include "esp_camera.h"
#include "esp_http_server.h"

const char* WIFI_SSID     = "YOUR_WIFI_SSID";   // 2.4 GHz
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// AI-Thinker pin map
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

static const char* STREAM_CT = "multipart/x-mixed-replace;boundary=ssframe";
static const char* STREAM_BOUNDARY = "\r\n--ssframe\r\n";
static const char* STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

httpd_handle_t mainServer = NULL;
httpd_handle_t streamServer = NULL;

static esp_err_t indexHandler(httpd_req_t* req) {
    char html[200];
    snprintf(html, sizeof(html),
             "<html><body><h3>Stock Shield CAM</h3><img src=\"http://%s:81/stream\" width=\"480\"></body></html>",
             WiFi.localIP().toString().c_str());
    httpd_resp_set_type(req, "text/html");
    return httpd_resp_send(req, html, HTTPD_RESP_USE_STRLEN);
}

static esp_err_t captureHandler(httpd_req_t* req) {
    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) { httpd_resp_send_500(req); return ESP_FAIL; }
    httpd_resp_set_type(req, "image/jpeg");
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    esp_err_t res = httpd_resp_send(req, (const char*)fb->buf, fb->len);
    esp_camera_fb_return(fb);
    return res;
}

static esp_err_t streamHandler(httpd_req_t* req) {
    esp_err_t res = httpd_resp_set_type(req, STREAM_CT);
    if (res != ESP_OK) return res;
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");

    char part[64];
    while (true) {
        camera_fb_t* fb = esp_camera_fb_get();
        if (!fb) { res = ESP_FAIL; break; }
        res = httpd_resp_send_chunk(req, STREAM_BOUNDARY, strlen(STREAM_BOUNDARY));
        if (res == ESP_OK) {
            size_t hlen = snprintf(part, sizeof(part), STREAM_PART, (unsigned)fb->len);
            res = httpd_resp_send_chunk(req, part, hlen);
        }
        if (res == ESP_OK) {
            res = httpd_resp_send_chunk(req, (const char*)fb->buf, fb->len);
        }
        esp_camera_fb_return(fb);
        if (res != ESP_OK) break;   // client disconnected
    }
    return res;
}

void startServers() {
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    httpd_uri_t indexUri   = {"/", HTTP_GET, indexHandler, NULL};
    httpd_uri_t captureUri = {"/capture", HTTP_GET, captureHandler, NULL};
    httpd_uri_t streamUri  = {"/stream", HTTP_GET, streamHandler, NULL};

    config.server_port = 80;
    if (httpd_start(&mainServer, &config) == ESP_OK) {
        httpd_register_uri_handler(mainServer, &indexUri);
        httpd_register_uri_handler(mainServer, &captureUri);
    }
    config.server_port = 81;
    config.ctrl_port += 1;
    if (httpd_start(&streamServer, &config) == ESP_OK) {
        httpd_register_uri_handler(streamServer, &streamUri);
    }
}

void setup() {
    Serial.begin(115200);
    delay(500);

    camera_config_t c;
    c.ledc_channel = LEDC_CHANNEL_0;
    c.ledc_timer = LEDC_TIMER_0;
    c.pin_d0 = Y2_GPIO_NUM;  c.pin_d1 = Y3_GPIO_NUM;
    c.pin_d2 = Y4_GPIO_NUM;  c.pin_d3 = Y5_GPIO_NUM;
    c.pin_d4 = Y6_GPIO_NUM;  c.pin_d5 = Y7_GPIO_NUM;
    c.pin_d6 = Y8_GPIO_NUM;  c.pin_d7 = Y9_GPIO_NUM;
    c.pin_xclk = XCLK_GPIO_NUM;
    c.pin_pclk = PCLK_GPIO_NUM;
    c.pin_vsync = VSYNC_GPIO_NUM;
    c.pin_href = HREF_GPIO_NUM;
    c.pin_sccb_sda = SIOD_GPIO_NUM;
    c.pin_sccb_scl = SIOC_GPIO_NUM;
    c.pin_pwdn = PWDN_GPIO_NUM;
    c.pin_reset = RESET_GPIO_NUM;
    c.xclk_freq_hz = 20000000;
    c.pixel_format = PIXFORMAT_JPEG;
    c.frame_size = FRAMESIZE_VGA;      // 640x480
    c.jpeg_quality = 12;
    c.fb_count = psramFound() ? 2 : 1;
    c.fb_location = psramFound() ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;
    c.grab_mode = CAMERA_GRAB_LATEST;

    if (esp_camera_init(&c) != ESP_OK) {
        Serial.println("Camera init failed (check ribbon cable)");
        return;
    }

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    Serial.print("WiFi");
    while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
    Serial.printf("\nStream: http://%s:81/stream\n", WiFi.localIP().toString().c_str());
    startServers();
}

void loop() { delay(10000); }
