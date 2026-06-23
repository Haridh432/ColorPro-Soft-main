/*
 * ============================================================
 *  ColorPro — ESP32 Shade Tester  (Full Working Code)
 *  AS7341 11-Channel Light Sensor  +  4 Touch Buttons
 *  Wi-Fi  +  Backend API  +  1.3" SPI OLED Menu System
 *
 *  Hardware Connections:
 *  ─────────────────────────────────────────────────────────
 *  OLED 1.3" SH1106 (SPI):
 *    SCK  → GPIO 18    MOSI → GPIO 23
 *    DC   → GPIO 16    CS   → GPIO 5     RST → GPIO 17
 *
 *  AS7341 Color Sensor (I2C):
 *    SDA  → GPIO 21    SCL  → GPIO 22
 *    LED  → GPIO 4  (sensor illumination LED)
 *
 *  Touch Buttons (Active HIGH):
 *    BTN_UP     → GPIO 32
 *    BTN_DOWN   → GPIO 33
 *    BTN_SELECT → GPIO 25
 *    BTN_BACK   → GPIO 26
 *
 *  Required Libraries (Arduino Library Manager):
 *    - Adafruit SH110X
 *    - Adafruit GFX
 *    - Adafruit AS7341
 *    - ArduinoJson (v7)
 * ============================================================
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>
#include <Adafruit_AS7341.h>
#include <ArduinoJson.h>

// ===================== USER CONFIG ==========================
const char* WIFI_SSID     = "protosem";
const char* WIFI_PASSWORD = "proto123";
const char* SERVER_IP     = "192.168.56.126";   // Your PC's LAN IP
const int   SERVER_PORT   = 8000;
// ============================================================

// ─── OLED (1.3" 128×64, SPI) ────────────────────────────────
#define OLED_DC     16
#define OLED_CS     5
#define OLED_RST    17

Adafruit_SH1106G oled(128, 64, &SPI, OLED_DC, OLED_RST, OLED_CS);

// ─── AS7341 Color Sensor (I2C) ────────────────────────────
#define SENSOR_LED_PIN 4
Adafruit_AS7341 as7341 = Adafruit_AS7341();
bool sensorReady = false;

// ─── Touch Buttons (Active HIGH) ────────────────────────────
#define BTN_UP      32
#define BTN_DOWN    33
#define BTN_SELECT  25
#define BTN_BACK    26

// Debounce
unsigned long lastBtnTime[4] = {0, 0, 0, 0};
const unsigned long DEBOUNCE_MS = 200;

enum ButtonPress { BTN_NONE, BTN_UP_PRESS, BTN_DOWN_PRESS, BTN_SELECT_PRESS, BTN_BACK_PRESS };

// ─── Application Screens ────────────────────────────────────
enum Screen {
  SCREEN_HOME,        // Status dashboard
  SCREEN_BATCHES,     // Batch list (fetched from server)
  SCREEN_ROLLS,       // Roll queue for selected batch
  SCREEN_SCANNING,    // Live scan screen
  SCREEN_RESULTS      // Scan result + Hold option
};

Screen currentScreen = SCREEN_HOME;

// ─── State ──────────────────────────────────────────────────
bool   serverOnline  = false;
int    pingCode      = 0;
String localIP       = "---";
unsigned long lastPing = 0;
const  unsigned long PING_EVERY = 10000;  // 10 s

// ── Batch list state ──
struct BatchInfo {
  String id;
  String name;
  int    rollCount;
  int    scannedCount;
};
BatchInfo batches[20];
int batchCount = 0;
int batchCursor = 0;     // highlighted index
int batchScrollTop = 0;  // scroll offset

// ── Roll list state ──
struct RollInfo {
  String id;
  String rollNumber;
  String status;
  bool   isHeld;
  int    scanCount;
  int    order;
};
RollInfo rolls[50];
int  rollCount = 0;
int  rollCursor = 0;
int  rollScrollTop = 0;
String currentBatchId   = "";
String currentBatchName = "";

// ── Scan result state ──
String currentRollId   = "";
String currentRollName = "";
float  lastL = 0, lastA = 0, lastBval = 0;
bool   scanSubmitted = false;
String scanResultStatus = "";

// ── Animation ──
bool   needsRedraw = true;
unsigned long lastAnimFrame = 0;
int    animFrame = 0;

// ─── Build API URL ──────────────────────────────────────────
String apiUrl(const char* path) {
  return "http://" + String(SERVER_IP) + ":" + String(SERVER_PORT) + path;
}

String apiUrl(String path) {
  return "http://" + String(SERVER_IP) + ":" + String(SERVER_PORT) + path;
}

// ═════════════════════════════════════════════════════════════
//  BUTTON HANDLING (Touch module is Active HIGH)
// ═════════════════════════════════════════════════════════════
ButtonPress readButtons() {
  unsigned long now = millis();

  if (digitalRead(BTN_UP) == HIGH && now - lastBtnTime[0] > DEBOUNCE_MS) {
    lastBtnTime[0] = now;
    return BTN_UP_PRESS;
  }
  if (digitalRead(BTN_DOWN) == HIGH && now - lastBtnTime[1] > DEBOUNCE_MS) {
    lastBtnTime[1] = now;
    return BTN_DOWN_PRESS;
  }
  if (digitalRead(BTN_SELECT) == HIGH && now - lastBtnTime[2] > DEBOUNCE_MS) {
    lastBtnTime[2] = now;
    return BTN_SELECT_PRESS;
  }
  if (digitalRead(BTN_BACK) == HIGH && now - lastBtnTime[3] > DEBOUNCE_MS) {
    lastBtnTime[3] = now;
    return BTN_BACK_PRESS;
  }
  return BTN_NONE;
}

// ═════════════════════════════════════════════════════════════
//  NETWORK HELPERS
// ═════════════════════════════════════════════════════════════

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.printf("[WiFi] Connecting to %s ...\n", WIFI_SSID);

  oled.clearDisplay();
  oled.setTextSize(1);
  oled.setTextColor(SH110X_WHITE);
  oled.setCursor(0, 0);
  oled.println("Connecting to WiFi");
  oled.println(WIFI_SSID);
  oled.display();

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int tries = 0;
  while (WiFi.status() != WL_CONNECTED && tries < 40) {
    delay(500);
    Serial.print(".");
    tries++;
    oled.print(".");
    oled.display();
  }

  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    localIP = WiFi.localIP().toString();
    Serial.printf("[WiFi] Connected! IP: %s\n", localIP.c_str());
  } else {
    Serial.println("[WiFi] Failed to connect");
    localIP = "N/A";
  }
}

void pingServer() {
  if (WiFi.status() != WL_CONNECTED) {
    serverOnline = false;
    pingCode = 0;
    return;
  }

  HTTPClient http;
  http.begin(apiUrl("/api/device/ping/"));
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000);

  pingCode = http.POST("{}");
  serverOnline = (pingCode == 200);

  if (pingCode == 200) {
    Serial.println("[Ping] Server: ONLINE");
  } else {
    Serial.printf("[Ping] Code: %d\n", pingCode);
  }
  http.end();
}

// ═════════════════════════════════════════════════════════════
//  API: FETCH BATCHES
// ═════════════════════════════════════════════════════════════
bool fetchBatches() {
  if (WiFi.status() != WL_CONNECTED || !serverOnline) return false;

  // Show loading
  oled.clearDisplay();
  oled.setTextSize(1);
  oled.setTextColor(SH110X_WHITE);
  oled.setCursor(20, 28);
  oled.print("Loading batches...");
  oled.display();

  HTTPClient http;
  http.begin(apiUrl("/api/batches/"));
  http.setTimeout(8000);
  int code = http.GET();

  if (code != 200) {
    Serial.printf("[API] Batch fetch failed: %d\n", code);
    http.end();
    return false;
  }

  String payload = http.getString();
  http.end();

  // Parse JSON
  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, payload);
  if (err) {
    Serial.printf("[JSON] Parse error: %s\n", err.c_str());
    return false;
  }

  // Handle Django REST Framework pagination (if 'results' key exists)
  JsonArray arr;
  if (doc.containsKey("results")) {
    arr = doc["results"].as<JsonArray>();
  } else {
    arr = doc.as<JsonArray>();
  }
  
  batchCount = 0;
  for (JsonObject obj : arr) {
    if (batchCount >= 20) break;
    batches[batchCount].id           = obj["id"].as<String>();
    batches[batchCount].name         = obj["name"].as<String>();
    batches[batchCount].rollCount    = obj["roll_count"] | 0;
    batches[batchCount].scannedCount = obj["scanned_count"] | 0;
    batchCount++;
  }

  Serial.printf("[API] Fetched %d batches\n", batchCount);
  batchCursor = 0;
  batchScrollTop = 0;
  return true;
}

// ═════════════════════════════════════════════════════════════
//  API: FETCH ROLLS FOR A BATCH
// ═════════════════════════════════════════════════════════════
bool fetchRolls(String batchId) {
  if (WiFi.status() != WL_CONNECTED || !serverOnline) return false;

  oled.clearDisplay();
  oled.setTextSize(1);
  oled.setTextColor(SH110X_WHITE);
  oled.setCursor(24, 28);
  oled.print("Loading rolls...");
  oled.display();

  HTTPClient http;
  String url = "/api/device/batch/" + batchId + "/rolls/";
  http.begin(apiUrl(url));
  http.setTimeout(8000);
  int code = http.GET();

  if (code != 200) {
    Serial.printf("[API] Roll fetch failed: %d\n", code);
    http.end();
    return false;
  }

  String payload = http.getString();
  http.end();

  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, payload);
  if (err) {
    Serial.printf("[JSON] Parse error: %s\n", err.c_str());
    return false;
  }

  currentBatchId   = batchId;
  currentBatchName = doc["batch_name"] | "Batch";

  JsonArray arr = doc["rolls"].as<JsonArray>();
  rollCount = 0;
  for (JsonObject obj : arr) {
    if (rollCount >= 50) break;
    rolls[rollCount].id         = obj["id"].as<String>();
    rolls[rollCount].rollNumber = obj["roll_number"].as<String>();
    rolls[rollCount].status     = obj["status"].as<String>();
    rolls[rollCount].isHeld     = obj["is_held"] | false;
    rolls[rollCount].scanCount  = obj["scan_count"] | 0;
    rolls[rollCount].order      = obj["order"] | 0;
    rollCount++;
  }

  Serial.printf("[API] Fetched %d rolls for batch %s\n", rollCount, currentBatchName.c_str());
  rollCursor = 0;
  rollScrollTop = 0;
  return true;
}

// ═════════════════════════════════════════════════════════════
//  API: SUBMIT SCAN
// ═════════════════════════════════════════════════════════════
bool submitScan(String batchId, String rollId, float L, float a, float b) {
  if (WiFi.status() != WL_CONNECTED) return false;

  HTTPClient http;
  http.begin(apiUrl("/api/scans/device/"));
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(8000);

  // Build JSON
  JsonDocument doc;
  doc["batch_id"] = batchId;
  doc["roll_id"]  = rollId;
  JsonArray labArr = doc["lab"].to<JsonArray>();
  labArr.add(L);
  labArr.add(a);
  labArr.add(b);

  String body;
  serializeJson(doc, body);

  Serial.printf("[Scan] Submitting LAB(%.1f, %.1f, %.1f) for roll %s\n", L, a, b, rollId.c_str());

  int code = http.POST(body);
  if (code == 201) {
    String resp = http.getString();
    http.end();

    JsonDocument respDoc;
    deserializeJson(respDoc, resp);
    lastL = respDoc["lab"]["l"] | 0.0;
    lastA = respDoc["lab"]["a"] | 0.0;
    lastBval = respDoc["lab"]["b"] | 0.0;
    scanResultStatus = respDoc["roll_status"].as<String>();
    scanSubmitted = true;

    Serial.printf("[Scan] OK — L*=%.1f a*=%.1f b*=%.1f status=%s\n",
                  lastL, lastA, lastBval, scanResultStatus.c_str());
    return true;
  } else {
    Serial.printf("[Scan] Submit failed: %d\n", code);
    http.end();
    return false;
  }
}

// ═════════════════════════════════════════════════════════════
//  API: HOLD ROLL
// ═════════════════════════════════════════════════════════════
bool holdRoll(String rollId) {
  if (WiFi.status() != WL_CONNECTED) return false;

  HTTPClient http;
  String url = "/api/device/roll/" + rollId + "/hold/";
  http.begin(apiUrl(url));
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000);

  // PATCH with empty body
  int code = http.PATCH("{}");
  bool ok = (code == 200);
  http.end();

  if (ok) Serial.printf("[Hold] Roll %s held\n", rollId.c_str());
  else    Serial.printf("[Hold] Failed: %d\n", code);

  return ok;
}

// ═════════════════════════════════════════════════════════════
//  COLOR MATH
// ═════════════════════════════════════════════════════════════
void XYZtoLAB(float X, float Y, float Z, float &L, float &a, float &b) {
  // Illuminant D65
  float Xn = 95.047f, Yn = 100.000f, Zn = 108.883f;
  float x = X / Xn, y = Y / Yn, z = Z / Zn;

  auto f = [](float t) {
    if (t > 0.008856f) return pow(t, 1.0f / 3.0f);
    else return (7.787f * t) + (16.0f / 116.0f);
  };

  float fx = f(x), fy = f(y), fz = f(z);
  L = (116.0f * fy) - 16.0f;
  a = 500.0f * (fx - fy);
  b = 200.0f * (fy - fz);
}

// ═════════════════════════════════════════════════════════════
//  COLOR SENSOR: READ LAB (AS7341)
// ═════════════════════════════════════════════════════════════
bool readColorSensor(float &L, float &a, float &b) {
  if (!sensorReady) return false;

  // Turn on LED
  digitalWrite(SENSOR_LED_PIN, HIGH);
  delay(100);   // Let sensor stabilize

  // Note: AS7341 needs to read channels. readAllChannels handles multiplexing.
  uint16_t readings[12];
  if (!as7341.readAllChannels(readings)) {
    digitalWrite(SENSOR_LED_PIN, LOW);
    return false;
  }
  digitalWrite(SENSOR_LED_PIN, LOW);

  // For AS7341: clear channel is index 10 (AS7341_CLEAR)
  uint16_t clear = readings[10];
  if (clear == 0) return false;  // No light detected

  // Approximate XYZ from spectral channels
  // Using F6 (~630nm) for Red, F4 (~515nm) for Green, F2 (~445nm) for Blue
  float X = (readings[5] * 1.1f) + (readings[1] * 0.2f);
  float Y = readings[3] * 1.0f;
  float Z = readings[1] * 1.2f;

  // Scale relative to clear channel
  float scale = 100.0f / (float)clear;
  X *= scale;
  Y *= scale;
  Z *= scale;

  XYZtoLAB(X, Y, Z, L, a, b);

  return true;
}

// ═════════════════════════════════════════════════════════════
//  DISPLAY: DRAW HELPERS
// ═════════════════════════════════════════════════════════════

// Draw a horizontal title bar
void drawTitleBar(const char* title) {
  oled.setTextSize(1);
  oled.setTextColor(SH110X_WHITE);

  // Filled bar
  oled.fillRect(0, 0, 128, 10, SH110X_WHITE);
  oled.setTextColor(SH110X_BLACK);

  // Center title
  int tw = strlen(title) * 6;
  int tx = (128 - tw) / 2;
  oled.setCursor(tx, 1);
  oled.print(title);

  // Reset color
  oled.setTextColor(SH110X_WHITE);
}

// Draw bottom nav hint bar
void drawNavBar(const char* left, const char* right) {
  oled.drawLine(0, 54, 127, 54, SH110X_WHITE);
  oled.setTextSize(1);
  oled.setCursor(0, 56);
  oled.print(left);

  int rw = strlen(right) * 6;
  oled.setCursor(128 - rw, 56);
  oled.print(right);
}

// Draw a scrollable list item (highlighted or normal)
void drawListItem(int y, const char* text, bool selected) {
  if (selected) {
    oled.fillRect(0, y, 128, 10, SH110X_WHITE);
    oled.setTextColor(SH110X_BLACK);
  } else {
    oled.setTextColor(SH110X_WHITE);
  }
  oled.setCursor(2, y + 1);
  oled.print(text);
  oled.setTextColor(SH110X_WHITE);  // reset
}

// ═════════════════════════════════════════════════════════════
//  SCREEN RENDERERS
// ═════════════════════════════════════════════════════════════

// ── SCREEN_HOME: Status Dashboard ───────────────────────────
void drawHomeScreen() {
  oled.clearDisplay();
  drawTitleBar("ColorPro Home");

  oled.setTextSize(1);

  // WiFi status
  oled.setCursor(0, 13);
  oled.print("WiFi: ");
  if (WiFi.status() == WL_CONNECTED) {
    oled.println("Connected");
    oled.setCursor(0, 23);
    oled.print("IP: ");
    oled.println(localIP);
  } else {
    oled.println("OFFLINE");
  }

  // Server status
  oled.setCursor(0, 33);
  oled.print("Server: ");
  oled.println(serverOnline ? "ONLINE" : "OFFLINE");

  // Sensor status
  oled.setCursor(0, 43);
  oled.print("Sensor: ");
  oled.println(sensorReady ? "OK" : "NOT FOUND");

  drawNavBar("", "SELECT>Batches");
  oled.display();
}

// ── SCREEN_BATCHES: Batch List ──────────────────────────────
void drawBatchScreen() {
  oled.clearDisplay();
  drawTitleBar("Select Batch");

  if (batchCount == 0) {
    oled.setCursor(16, 28);
    oled.print("No batches found");
    drawNavBar("<BACK", "");
    oled.display();
    return;
  }

  // Draw visible items (4 rows fit between title bar and nav bar)
  const int VISIBLE = 4;
  const int ROW_H   = 10;
  const int START_Y = 12;

  // Auto-scroll so cursor is always visible
  if (batchCursor < batchScrollTop) batchScrollTop = batchCursor;
  if (batchCursor >= batchScrollTop + VISIBLE) batchScrollTop = batchCursor - VISIBLE + 1;

  for (int i = 0; i < VISIBLE; i++) {
    int idx = batchScrollTop + i;
    if (idx >= batchCount) break;

    char line[26];
    snprintf(line, sizeof(line), "%-14s %d/%d",
             batches[idx].name.substring(0, 14).c_str(),
             batches[idx].scannedCount,
             batches[idx].rollCount);

    drawListItem(START_Y + i * ROW_H, line, idx == batchCursor);
  }

  // Scroll indicator
  if (batchCount > VISIBLE) {
    int barH = max(4, (VISIBLE * (VISIBLE * ROW_H)) / batchCount);
    int barY = START_Y + (batchScrollTop * (VISIBLE * ROW_H - barH)) / max(1, batchCount - VISIBLE);
    oled.fillRect(126, barY, 2, barH, SH110X_WHITE);
  }

  drawNavBar("<BACK", "SELECT>");
  oled.display();
}

// ── SCREEN_ROLLS: Roll Queue ────────────────────────────────
void drawRollScreen() {
  oled.clearDisplay();

  char title[24];
  snprintf(title, sizeof(title), "%s", currentBatchName.substring(0, 20).c_str());
  drawTitleBar(title);

  if (rollCount == 0) {
    oled.setCursor(16, 28);
    oled.print("No rolls in batch");
    drawNavBar("<BACK", "");
    oled.display();
    return;
  }

  const int VISIBLE = 4;
  const int ROW_H   = 10;
  const int START_Y = 12;

  if (rollCursor < rollScrollTop) rollScrollTop = rollCursor;
  if (rollCursor >= rollScrollTop + VISIBLE) rollScrollTop = rollCursor - VISIBLE + 1;

  for (int i = 0; i < VISIBLE; i++) {
    int idx = rollScrollTop + i;
    if (idx >= rollCount) break;

    // Status icon
    char icon = ' ';
    if (rolls[idx].isHeld)                       icon = 'H';
    else if (rolls[idx].status == "accepted")    icon = '+';
    else if (rolls[idx].status == "warning")     icon = '!';
    else if (rolls[idx].status == "rejected")    icon = 'X';
    else if (rolls[idx].status == "scanned")     icon = '*';
    else                                         icon = '-';  // pending

    char line[26];
    snprintf(line, sizeof(line), "%c %-12s  S:%d",
             icon,
             rolls[idx].rollNumber.substring(0, 12).c_str(),
             rolls[idx].scanCount);

    drawListItem(START_Y + i * ROW_H, line, idx == rollCursor);
  }

  // Scroll indicator
  if (rollCount > VISIBLE) {
    int barH = max(4, (VISIBLE * (VISIBLE * ROW_H)) / rollCount);
    int barY = START_Y + (rollScrollTop * (VISIBLE * ROW_H - barH)) / max(1, rollCount - VISIBLE);
    oled.fillRect(126, barY, 2, barH, SH110X_WHITE);
  }

  drawNavBar("<BACK", "SELECT>Scan");
  oled.display();
}

// ── SCREEN_SCANNING: Live Scan ──────────────────────────────
void drawScanningScreen() {
  oled.clearDisplay();
  drawTitleBar("Scanning...");

  oled.setTextSize(1);
  oled.setCursor(0, 14);
  oled.print("Roll: ");
  oled.println(currentRollName.substring(0, 14));

  // Animated indicator
  unsigned long now = millis();
  if (now - lastAnimFrame > 300) {
    animFrame = (animFrame + 1) % 4;
    lastAnimFrame = now;
  }
  const char* spinner[] = {"|", "/", "-", "\\"};

  oled.setCursor(56, 30);
  oled.setTextSize(2);
  oled.print(spinner[animFrame]);
  oled.setTextSize(1);

  oled.setCursor(8, 48);
  oled.print("Place fabric on sensor");

  drawNavBar("<BACK:Cancel", "SEL:Capture");
  oled.display();
}

// ── SCREEN_RESULTS: Scan Results ────────────────────────────
void drawResultsScreen() {
  oled.clearDisplay();
  drawTitleBar("Scan Result");

  oled.setTextSize(1);

  // Roll name
  oled.setCursor(0, 12);
  oled.print("Roll: ");
  oled.println(currentRollName.substring(0, 14));

  // Display LAB values (calculated locally)
  oled.setCursor(0, 22);
  char labLine[28];
  char lStr[8], aStr[8], bStr[8];
  dtostrf(lastL, 4, 1, lStr);
  dtostrf(lastA, 4, 1, aStr);
  dtostrf(lastBval, 4, 1, bStr);
  snprintf(labLine, sizeof(labLine), "LAB: %s %s %s", lStr, aStr, bStr);
  oled.println(labLine);

  // Status (from server response)
  if (scanSubmitted) {
    oled.setCursor(0, 36);
    oled.print("Status: ");
    oled.println(scanResultStatus);
  } else {
    oled.setCursor(0, 36);
    oled.println("Submitting...");
  }

  // Color preview swatch (small filled rect)
  // We invert if the color is very light (so it's visible on white OLED)
  oled.fillRect(104, 12, 22, 22, SH110X_WHITE);
  oled.drawRect(103, 11, 24, 24, SH110X_WHITE);

  drawNavBar("<BACK", "SEL:Hold Roll");
  oled.display();
}

// ═════════════════════════════════════════════════════════════
//  INPUT HANDLING PER SCREEN
// ═════════════════════════════════════════════════════════════

void handleHomeInput(ButtonPress btn) {
  if (btn == BTN_SELECT_PRESS) {
    if (serverOnline) {
      if (fetchBatches()) {
        currentScreen = SCREEN_BATCHES;
        needsRedraw = true;
      }
    }
  }
}

void handleBatchInput(ButtonPress btn) {
  switch (btn) {
    case BTN_UP_PRESS:
      if (batchCursor > 0) { batchCursor--; needsRedraw = true; }
      break;
    case BTN_DOWN_PRESS:
      if (batchCursor < batchCount - 1) { batchCursor++; needsRedraw = true; }
      break;
    case BTN_SELECT_PRESS:
      if (batchCount > 0) {
        if (fetchRolls(batches[batchCursor].id)) {
          currentScreen = SCREEN_ROLLS;
          needsRedraw = true;
        }
      }
      break;
    case BTN_BACK_PRESS:
      currentScreen = SCREEN_HOME;
      needsRedraw = true;
      break;
    default: break;
  }
}

void handleRollInput(ButtonPress btn) {
  switch (btn) {
    case BTN_UP_PRESS:
      if (rollCursor > 0) { rollCursor--; needsRedraw = true; }
      break;
    case BTN_DOWN_PRESS:
      if (rollCursor < rollCount - 1) { rollCursor++; needsRedraw = true; }
      break;
    case BTN_SELECT_PRESS:
      if (rollCount > 0) {
        currentRollId   = rolls[rollCursor].id;
        currentRollName = rolls[rollCursor].rollNumber;
        scanSubmitted   = false;
        scanResultStatus = "";
        currentScreen   = SCREEN_SCANNING;
        needsRedraw     = true;
      }
      break;
    case BTN_BACK_PRESS:
      currentScreen = SCREEN_BATCHES;
      needsRedraw = true;
      break;
    default: break;
  }
}

void handleScanInput(ButtonPress btn) {
  switch (btn) {
    case BTN_SELECT_PRESS: {
      // Capture color reading
      float L, a, b;
      if (readColorSensor(L, a, b)) {
        lastL = L;
        lastA = a;
        lastBval = b;

        // Show "Uploading..." briefly
        oled.clearDisplay();
        oled.setTextSize(1);
        oled.setCursor(20, 28);
        oled.print("Uploading scan...");
        oled.display();

        // Submit to server
        submitScan(currentBatchId, currentRollId, L, a, b);

        currentScreen = SCREEN_RESULTS;
        needsRedraw = true;
      } else {
        // Sensor error
        oled.clearDisplay();
        oled.setTextSize(1);
        oled.setCursor(8, 24);
        oled.print("Sensor read failed!");
        oled.setCursor(8, 36);
        oled.print("Check wiring/fabric");
        oled.display();
        delay(1500);
        needsRedraw = true;
      }
      break;
    }
    case BTN_BACK_PRESS:
      currentScreen = SCREEN_ROLLS;
      needsRedraw = true;
      break;
    default: break;
  }
}

void handleResultsInput(ButtonPress btn) {
  switch (btn) {
    case BTN_SELECT_PRESS:
      // Hold Roll
      if (holdRoll(currentRollId)) {
        oled.clearDisplay();
        oled.setTextSize(1);
        oled.setCursor(16, 20);
        oled.print("Roll HELD");
        oled.setCursor(16, 34);
        oled.print(currentRollName);
        oled.display();
        delay(1200);
      }
      // Refresh rolls and go back
      fetchRolls(currentBatchId);
      currentScreen = SCREEN_ROLLS;
      needsRedraw = true;
      break;

    case BTN_BACK_PRESS:
      // Go back to roll list (refresh to show updated scan count)
      fetchRolls(currentBatchId);
      currentScreen = SCREEN_ROLLS;
      needsRedraw = true;
      break;

    case BTN_UP_PRESS:
      // Re-scan (go back to scanning for same roll)
      scanSubmitted = false;
      currentScreen = SCREEN_SCANNING;
      needsRedraw = true;
      break;

    default: break;
  }
}

// ═════════════════════════════════════════════════════════════
//  SETUP
// ═════════════════════════════════════════════════════════════
void setup() {
  Serial.begin(115200);
  Serial.println("\n===== ColorPro ESP32 Shade Tester =====");

  // ── Button pins (Touch module, Active HIGH) ──
  // Using INPUT_PULLDOWN to prevent floating pins that cause constant flickering
  pinMode(BTN_UP,     INPUT_PULLDOWN);
  pinMode(BTN_DOWN,   INPUT_PULLDOWN);
  pinMode(BTN_SELECT, INPUT_PULLDOWN);
  pinMode(BTN_BACK,   INPUT_PULLDOWN);

  // ── Sensor LED ──
  pinMode(SENSOR_LED_PIN, OUTPUT);
  digitalWrite(SENSOR_LED_PIN, LOW);

  // ── Init SPI OLED ──
  if (!oled.begin(0, true)) {
    Serial.println("[OLED] Init FAILED — check wiring");
    for (;;);
  }
  oled.clearDisplay();
  oled.display();

  // ── Splash screen ──
  oled.setTextSize(2);
  oled.setTextColor(SH110X_WHITE);
  oled.setCursor(10, 4);
  oled.println("ColorPro");
  oled.setTextSize(1);
  oled.setCursor(20, 26);
  oled.println("Shade Tester v2.0");
  oled.setCursor(20, 40);
  oled.println("4-Button Nav");
  oled.setCursor(20, 52);
  oled.println("Initializing...");
  oled.display();
  delay(1500);

  // ── Init I2C Color Sensor ──
  Wire.begin(21, 22);  // SDA=21, SCL=22
  if (as7341.begin()) {
    sensorReady = true;
    as7341.setGain(AS7341_GAIN_256X);
    as7341.setATIME(29);
    as7341.setASTEP(599);
    Serial.println("[Sensor] AS7341 found");
  } else {
    sensorReady = false;
    Serial.println("[Sensor] AS7341 NOT found — continuing without sensor");
  }

  // ── Connect WiFi ──
  connectWiFi();

  // ── First ping ──
  pingServer();
  lastPing = millis();

  // ── Start on Home screen ──
  currentScreen = SCREEN_HOME;
  needsRedraw = true;
}

// ═════════════════════════════════════════════════════════════
//  LOOP
// ═════════════════════════════════════════════════════════════
void loop() {
  unsigned long now = millis();

  // ── Reconnect WiFi if dropped ──
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  // ── Background ping every PING_EVERY ms ──
  if (now - lastPing >= PING_EVERY) {
    pingServer();
    lastPing = now;
    if (currentScreen == SCREEN_HOME) needsRedraw = true;
  }

  // ── Read buttons ──
  ButtonPress btn = readButtons();

  // ── Dispatch input to current screen ──
  if (btn != BTN_NONE) {
    switch (currentScreen) {
      case SCREEN_HOME:     handleHomeInput(btn);     break;
      case SCREEN_BATCHES:  handleBatchInput(btn);    break;
      case SCREEN_ROLLS:    handleRollInput(btn);     break;
      case SCREEN_SCANNING: handleScanInput(btn);     break;
      case SCREEN_RESULTS:  handleResultsInput(btn);  break;
    }
  }

  // ── Scanning screen animates continuously ──
  if (currentScreen == SCREEN_SCANNING) {
    needsRedraw = true;
  }

  // ── Redraw screen if needed ──
  if (needsRedraw) {
    switch (currentScreen) {
      case SCREEN_HOME:     drawHomeScreen();     break;
      case SCREEN_BATCHES:  drawBatchScreen();    break;
      case SCREEN_ROLLS:    drawRollScreen();     break;
      case SCREEN_SCANNING: drawScanningScreen(); break;
      case SCREEN_RESULTS:  drawResultsScreen();  break;
    }
    needsRedraw = false;
  }

  delay(50);  // Small delay to prevent busy-looping
}