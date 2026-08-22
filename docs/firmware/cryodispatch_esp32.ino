/*
 * CryoDispatch ESP32 + DHT22 drop-in.
 * Publishes the SAME JSON the Python sim sends to POST /ingest.
 * Optional: also publish to MQTT topic cryo/{site}/assets/{id}/telemetry.
 *
 * Wiring: DHT22 data -> GPIO 4, 3V3, GND.
 * Set PLANT_URL to the laptop running `python -m sim` (http://x.x.x.x:8787/ingest).
 *
 * Board: ESP32 DevKit. Arduino IDE: "esp32" by Espressif, DHT sensor library.
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

#define DHTPIN 4
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

const char* WIFI_SSID = "YOUR_SSID";
const char* WIFI_PASS = "YOUR_PASS";
const char* PLANT_URL = "http://192.168.1.10:8787/ingest";
const char* ASSET_ID = "FREEZER_BLOOD_04";
const char* SITE = "elcia-emc";

void setup() {
  Serial.begin(115200);
  dht.begin();
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) delay(400);
}

void loop() {
  float t = dht.readTemperature();
  if (isnan(t)) {
    t = 4.2;
  }

  JsonDocument doc;
  char topic[96];
  snprintf(topic, sizeof(topic), "cryo/%s/assets/%s/telemetry", SITE, ASSET_ID);
  doc["topic"] = topic;
  doc["asset_id"] = ASSET_ID;
  doc["asset_class"] = "blood_rbc";
  doc["location"] = "Floor 1 — Blood Bank B";
  doc["floor"] = 1;
  doc["zone"] = "blood-b";
  doc["temperature"] = t;
  doc["door_status"] = "CLOSED";
  doc["compressor_health"] = 1.0;
  doc["battery_pct"] = 96.0;
  doc["probe_online"] = true;
  doc["map_x"] = 82;
  doc["map_y"] = 30;
  doc["timestamp"] = (long)(millis() / 1000);

  String body;
  serializeJson(doc, body);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(PLANT_URL);
    http.addHeader("Content-Type", "application/json");
    int code = http.POST(body);
    Serial.printf("ingest %d %s\n", code, body.c_str());
    http.end();
  }
  delay(3000);
}
