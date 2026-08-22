/*
 * CryoDispatch ESP32 + DHT22 drop-in.
 * Publishes the SAME JSON the Python sim sends to POST /ingest, so real hardware
 * can replace apps/sim without touching the plant, the dashboard, or the app.
 *
 * A failed read reports probe_online=false and omits the temperature. It never
 * invents a plausible number: that is the whole point of the PROBE_DEAD class.
 * Pull the sensor and the plant should raise a ticket, not evacuate stock.
 *
 * Wiring: DHT22 data -> GPIO 4, 3V3, GND.
 * Set PLANT_URL to the laptop running `python -m sim` (http://x.x.x.x:8787/ingest).
 * Do not post at the Supabase ingest function — that path is gone. The plant
 * decides; Supabase only stores what it already decided.
 *
 * Board: ESP32 DevKit.
 * Libraries: "esp32" by Espressif, "DHT sensor library" (Adafruit) plus its
 * "Adafruit Unified Sensor" dependency, and "ArduinoJson" v7 (this sketch uses
 * the v7 JsonDocument API; on v6 use StaticJsonDocument<512> instead).
 *
 * MQTT is intentionally not included here. The broker path is a documented
 * contract (docs/mqtt-schema.md); the demo ingests over HTTP so a broker outage
 * cannot take the plant down.
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

#include <time.h>

#define DHTPIN 4
#define DOOR_PIN 5   // reed switch: HIGH = open
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
  pinMode(DOOR_PIN, INPUT_PULLDOWN);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) delay(400);
  // The plant timestamps its own readings, but a real logger needs epoch time
  // for the custody record, so sync once we have a network.
  configTime(19800, 0, "pool.ntp.org");  // +05:30 IST
}

/** Epoch seconds, falling back to uptime before the first NTP sync. */
long epochSeconds() {
  time_t now = time(nullptr);
  return now > 1600000000 ? (long)now : (long)(millis() / 1000);
}

/** Placeholder for a current-clamp reading. 1.0 = healthy, 0.0 = failed. */
float compressorHealth() {
  return 1.0;
}

void loop() {
  float t = dht.readTemperature();
  bool probeOk = !isnan(t);

  JsonDocument doc;
  char topic[96];
  snprintf(topic, sizeof(topic), "cryo/%s/assets/%s/telemetry", SITE, ASSET_ID);
  doc["topic"] = topic;
  doc["asset_id"] = ASSET_ID;
  doc["asset_class"] = "blood_rbc";
  doc["location"] = "Floor 1 — Blood Bank B";
  doc["floor"] = 1;
  doc["zone"] = "blood-b";
  if (probeOk) {
    doc["temperature"] = t;
  } else {
    doc["temperature"] = (const char*)nullptr;  // null, never a guess
  }
  doc["door_status"] = digitalRead(DOOR_PIN) == HIGH ? "OPEN" : "CLOSED";
  // Duty-cycle proxy: a healthy compressor rests. Wire a current clamp for real data.
  doc["compressor_health"] = compressorHealth();
  doc["battery_pct"] = 96.0;
  doc["probe_online"] = probeOk;
  doc["map_x"] = 82;
  doc["map_y"] = 30;
  doc["timestamp"] = epochSeconds();

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
