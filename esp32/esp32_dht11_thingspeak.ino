#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h"

/* -------- USER CONFIG -------- */
const char* ssid = "Galaxy S23ultra";
const char* password = "eokekjgz";

String writeAPIKey = "89Q4XRJ8U1GJGYKF";
String readAPIKey  = "79SP1MV4ASBVHNBY";
String channelID   = "YOUR_CHANNEL_ID";
/* ----------------------------- */

#define DHTPIN 4
#define DHTTYPE DHT11
#define LED_PIN 2

DHT dht(DHTPIN, DHTTYPE);

float temperature = 0.0;
float threshold = 30.0;   // default fallback value

unsigned long lastUpdate = 0;
const unsigned long interval = 20000; // 20 seconds (ThingSpeak safe)

/* -------- WiFi Setup -------- */
void connectWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

/* -------- Upload Temperature -------- */
void uploadTemperature(float temp) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = "http://api.thingspeak.com/update?api_key=" +
                  writeAPIKey + "&field1=" + String(temp);

    http.begin(url);
    int httpCode = http.GET();
    http.end();

    Serial.print("Upload response: ");
    Serial.println(httpCode);
  }
}

/* -------- Read Threshold -------- */
float readThreshold() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = "http://api.thingspeak.com/channels/" +
                 channelID + "/fields/2/last.txt?api_key=" + readAPIKey;

    http.begin(url);
    int httpCode = http.GET();

    if (httpCode == 200) {
      String payload = http.getString();
      http.end();
      return payload.toFloat();
    }
    http.end();
  }
  return threshold;  // fallback
}

/* -------- LED Alert -------- */
void blinkLED() {
  digitalWrite(LED_PIN, HIGH);
  delay(500);
  digitalWrite(LED_PIN, LOW);
  delay(500);
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  dht.begin();
  connectWiFi();
}

void loop() {
  if (millis() - lastUpdate >= interval) {
    lastUpdate = millis();

    temperature = dht.readTemperature();

    if (isnan(temperature)) {
      Serial.println("Failed to read DHT11");
      return;
    }

    Serial.print("Temperature: ");
    Serial.println(temperature);

    uploadTemperature(temperature);
    threshold = readThreshold();

    Serial.print("Threshold: ");
    Serial.println(threshold);

    if (temperature > threshold) {
      Serial.println("⚠ Temperature exceeded!");
      blinkLED();
    } else {
      digitalWrite(LED_PIN, LOW);
    }
  }
}

