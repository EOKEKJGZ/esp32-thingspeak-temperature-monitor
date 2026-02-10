#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "DHT.h"

/* -------- USER CONFIG -------- */
const char* ssid = "XYZ";
const char* password = "XYZ";

const char* WRITE_API_KEY = "XYZ";
const char* READ_API_KEY  = "XYZ";
const char* CHANNEL_ID    = "123";
/* ----------------------------- */

/* -------- OLED CONFIG -------- */
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define OLED_ADDR 0x3C

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

/* -------- SENSOR / ACTUATOR -------- */
#define DHTPIN 4
#define DHTTYPE DHT11
#define LED_PIN 2

DHT dht(DHTPIN, DHTTYPE);

/* -------- VARIABLES -------- */
float temperature = 0.0;
float humidity = 0.0;
float threshold = 30.0;

unsigned long lastUpdate = 0;
const unsigned long interval = 20000; // ThingSpeak rate limit

bool alertActive = false;

/* -------- OLED HELPERS -------- */
void showMessage(String l1, String l2 = "") {
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println(l1);
  if (l2 != "") {
    display.println();
    display.println(l2);
  }
  display.display();
}

void showWiFiConnected() {
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("WiFi: CONNECTED");
  display.println("----------------");
  display.print("SSID: ");
  display.println(WiFi.SSID());
  display.println();
  display.println("IP Address:");
  display.println(WiFi.localIP());
  display.display();
}

void showWiFiDisconnected() {
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("WiFi: DISCONNECTED");
  display.println("----------------");
  display.println("Reconnecting...");
  display.display();
}

/* -------- WIFI -------- */
void connectWiFi() {
  WiFi.begin(ssid, password);
  showMessage("Connecting WiFi", "Please wait...");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  showWiFiConnected();
}

/* -------- UPLOAD DATA -------- */
void uploadData(float temp, float hum) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    String url = "http://api.thingspeak.com/update?api_key=" +
                 String(WRITE_API_KEY) +
                 "&field1=" + String(temp) +
                 "&field3=" + String(hum);

    http.begin(url);
    http.GET();
    http.end();
  }
}

/* -------- READ THRESHOLD (FIELD 2) -------- */
float readThreshold() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    String url = "http://api.thingspeak.com/channels/" +
                 String(CHANNEL_ID) +
                 "/fields/2/last.txt?api_key=" +
                 String(READ_API_KEY);

    http.begin(url);
    int httpCode = http.GET();

    if (httpCode == 200) {
      float value = http.getString().toFloat();
      http.end();
      return value;
    }
    http.end();
  }
  return threshold;
}

/* -------- NON-BLOCKING LED BLINK -------- */
void handleLEDAlert() {
  static unsigned long lastBlink = 0;
  static bool ledState = false;

  if (!alertActive) {
    digitalWrite(LED_PIN, LOW);
    return;
  }

  if (millis() - lastBlink >= 300) {
    lastBlink = millis();
    ledState = !ledState;
    digitalWrite(LED_PIN, ledState);
  }
}

/* -------- SETUP -------- */
void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  dht.begin();
  Wire.begin(21, 22);

  if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
    while (true);
  }

  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);

  showMessage("ESP32 Booting...");
  delay(1500);

  connectWiFi();
}

/* -------- LOOP -------- */
void loop() {

  handleLEDAlert(); // runs continuously

  if (WiFi.status() != WL_CONNECTED) {
    showWiFiDisconnected();
    WiFi.reconnect();
    delay(2000);
    return;
  }

  if (millis() - lastUpdate >= interval) {
    lastUpdate = millis();

    temperature = dht.readTemperature();
    humidity = dht.readHumidity();

    if (isnan(temperature) || isnan(humidity)) {
      showMessage("Sensor Error", "Check DHT11");
      return;
    }

    uploadData(temperature, humidity);
    threshold = readThreshold();

    alertActive = temperature > threshold;

    /* -------- OLED -------- */
    display.clearDisplay();
    display.setCursor(0, 0);

    display.println("ESP32 STATUS");
    display.println("----------------");

    display.print("Temp: ");
    display.print(temperature);
    display.println(" C");

    display.print("Humidity: ");
    display.print(humidity);
    display.println(" %");

    display.print("Limit: ");
    display.print(threshold);
    display.println(" C");

    display.println();
    display.println(alertActive ? "ALERT: OVER TEMP!" : "Status: Normal");

    display.display();
  }
}


