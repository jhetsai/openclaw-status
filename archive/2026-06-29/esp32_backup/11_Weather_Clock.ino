// ESP32-S3-RLCD-4.2 Weather Clock + Portfolio
// Default: Indoor page (Clock + SHTC3 + Battery)
// Press KEY (GPIO18) → Portfolio page
#include "ST7305_U8g2.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <time.h>
#include <sys/time.h>
#include <Wire.h>

#define LCD_WIDTH  400
#define LCD_HEIGHT 300
#define RLCD_SCK_PIN   11
#define RLCD_MOSI_PIN  12
#define RLCD_DC_PIN     5
#define RLCD_CS_PIN    40
#define RLCD_RST_PIN   41

const char* WIFI_SSID = "IoT";
const char* WIFI_PASS = "057851463";
const char* NTP_SERVER = "pool.ntp.org";
const long   GMT_OFFSET = 8 * 3600;

#define RTC_ADDR     0x51
#define RTC_TIME_REG 0x04
#define KEY_PIN      18    // GPIO18 = KEY 按鍵

#define SHTC3_ADDR 0x70
#define SHTC3_CMD_MEAS_T_RH_POLLING 0x7866

const char* PORTFOLIO_URL =
  "https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/assets/esp32_portfolio.json";

static ST7305_U8g2 lcd(RLCD_SCK_PIN, RLCD_MOSI_PIN, RLCD_DC_PIN, RLCD_CS_PIN, RLCD_RST_PIN);
static U8G2 *u8g2 = nullptr;

enum Page { PAGE_INDOOR, PAGE_PORTFOLIO };
static Page currentPage = PAGE_INDOOR;
static bool portfolioLoaded = false;

static struct Pf {
  float total_cost, total_mkt, total_gain, total_gain_pct;
  float tw_cost, tw_mkt, tw_gain, tw_gain_pct;
  float us_cost_twd, us_mkt_twd, us_gain_twd, us_gain_pct;
  float usd_amount, usd_rate;
  float jpy_amount, jpy_rate;
  unsigned long lastFetch;
} pf = {0};

static int lh=0, lm=0, ls=0, ld=1, lmo=1, ly=2026;
static float lastTemp = 0, lastHum = 0;
static const char* lastStatus = "Starting...";

static unsigned long lastDisplay  = 0;
static unsigned long lastSensor   = 0;
static unsigned long lastKeyCheck = 0;
static unsigned long lastPfRefresh= 0;
static const unsigned long DISPLAY_MS = 1000UL;
static const unsigned long SENSOR_MS  = 5UL * 60 * 1000UL;
static const unsigned long KEY_MS     = 200UL;
static const unsigned long PF_REFRESH  = 15UL * 60 * 1000UL;

// ============================================================
void fmtComma(float v, char *out, int len) {
  bool neg = v < 0;
  if (neg) v = -v;
  unsigned long iv = (unsigned long)(v + 0.5f);
  char tmp[24];
  int p = 0, digits = 0;
  do {
    if (digits > 0 && digits % 3 == 0) tmp[p++] = ',';
    tmp[p++] = '0' + (iv % 10);
    iv /= 10; digits++;
  } while (iv > 0);
  if (neg) tmp[p++] = '-';
  for (int i = 0; i < p && i < len - 1; i++) out[i] = tmp[p - 1 - i];
  out[p < len ? p : len - 1] = '\0';
}

void drawCenteredStr(int y, const char *text) {
  int x = (LCD_WIDTH - u8g2->getStrWidth(text)) / 2;
  if (x < 0) x = 0;
  u8g2->drawStr(x, y, text);
}

void drawHLine(int x1, int y, int x2) {
  u8g2->drawHLine(x1, y, x2 - x1);
}

// ============================================================
int bcd2int(uint8_t b) { return (b / 16) * 10 + (b & 0x0F); }
uint8_t int2bcd(int v) { return ((v / 10) << 4) | (v % 10); }

bool getRTC(int &hour, int &minute, int &second, int &day, int &month, int &year) {
  Wire.beginTransmission(RTC_ADDR);
  Wire.write(RTC_TIME_REG);
  if (Wire.endTransmission() != 0) return false;
  Wire.requestFrom(RTC_ADDR, 7);
  if (Wire.available() < 7) return false;
  second = bcd2int(Wire.read() & 0x7F);
  minute = bcd2int(Wire.read() & 0x7F);
  hour   = bcd2int(Wire.read() & 0x3F);
  day    = bcd2int(Wire.read() & 0x3F);
  Wire.read();
  month  = bcd2int(Wire.read() & 0x1F);
  year   = bcd2int(Wire.read()) + 2000;
  return true;
}

void setRTC(int hour, int minute, int second, int day, int month, int year) {
  Wire.beginTransmission(RTC_ADDR);
  Wire.write(0x00); Wire.write(0x00); Wire.endTransmission();
  Wire.beginTransmission(RTC_ADDR);
  Wire.write(RTC_TIME_REG);
  Wire.write(int2bcd(second));
  Wire.write(int2bcd(minute));
  Wire.write(int2bcd(hour));
  Wire.write(int2bcd(day));
  Wire.write(0);
  Wire.write(int2bcd(month));
  Wire.write(int2bcd(year - 2000));
  Wire.endTransmission();
}

// ============================================================
bool shtc3_wakeup() {
  Wire.beginTransmission(SHTC3_ADDR);
  Wire.write(0x35); Wire.write(0x17);
  return Wire.endTransmission() == 0;
}

bool shtc3_soft_reset() {
  Wire.beginTransmission(SHTC3_ADDR);
  Wire.write(0x80); Wire.write(0x5D);
  if (Wire.endTransmission() != 0) return false;
  delay(2);
  return true;
}

bool shtc3_read(float &temp, float &humidity) {
  Wire.beginTransmission(SHTC3_ADDR);
  Wire.write((SHTC3_CMD_MEAS_T_RH_POLLING >> 8) & 0xFF);
  Wire.write(SHTC3_CMD_MEAS_T_RH_POLLING & 0xFF);
  if (Wire.endTransmission() != 0) return false;
  delay(20);
  Wire.requestFrom(SHTC3_ADDR, 6);
  if (Wire.available() < 6) return false;
  uint8_t d[6];
  for (int i = 0; i < 6; i++) d[i] = Wire.read();
  uint16_t tempRaw = ((uint16_t)d[0] << 8) | d[1];
  uint16_t humRaw  = ((uint16_t)d[3] << 8) | d[4];
  temp = -45.0f + 175.0f * ((float)tempRaw / 65535.0f);
  humidity = 100.0f * ((float)humRaw / 65535.0f);
  return true;
}

// ============================================================
float extractFloat(const char *json, const char *key) {
  const char *p = strstr(json, key);
  if (!p) return 0;
  p += strlen(key);
  while (*p && (*p < '0' || *p > '9') && *p != '-') p++;
  if (!*p) return 0;
  char *end;
  float v = strtof(p, &end);
  return v;
}

bool fetchPortfolio() {
  HTTPClient http;
  WiFiClientSecure client;
  client.setInsecure();
  if (!http.begin(client, PORTFOLIO_URL)) return false;
  http.setTimeout(15000);
  int code = http.GET();
  if (code != HTTP_CODE_OK) { http.end(); return false; }
  String payload = http.getString();
  http.end();
  const char *json = payload.c_str();

  pf.total_cost     = extractFloat(json, "\"total_cost\":");
  pf.total_mkt     = extractFloat(json, "\"total_mktval\":");
  pf.total_gain    = extractFloat(json, "\"total_gain\":");
  pf.total_gain_pct = extractFloat(json, "\"total_gain_pct\":");

  const char *twBlock = strstr(json, "\"tw\":");
  if (twBlock) {
    pf.tw_cost    = extractFloat(twBlock, "\"cost\":");
    pf.tw_mkt     = extractFloat(twBlock, "\"mktval\":");
    pf.tw_gain    = extractFloat(twBlock, "\"gain\":");
    pf.tw_gain_pct = extractFloat(twBlock, "\"gain_pct\":");
  }

  const char *usBlock = strstr(json, "\"us\":");
  if (usBlock) {
    pf.us_cost_twd = extractFloat(usBlock, "\"cost_twd\":");
    pf.us_mkt_twd  = extractFloat(usBlock, "\"mktval_twd\":");
    pf.us_gain_twd = extractFloat(usBlock, "\"gain_twd\":");
    pf.us_gain_pct = extractFloat(usBlock, "\"gain_pct\":");
  }

  const char *usdBlock = strstr(json, "\"usd\":");
  if (usdBlock) {
    pf.usd_amount = extractFloat(usdBlock, "\"amount\":");
    pf.usd_rate   = extractFloat(usdBlock, "\"rate_usd_twd\":");
  }

  const char *jpyBlock = strstr(json, "\"jpy\":");
  if (jpyBlock) {
    pf.jpy_amount = extractFloat(jpyBlock, "\"amount\":");
    pf.jpy_rate   = extractFloat(jpyBlock, "\"rate_jpy_twd\":");
  }

  pf.lastFetch = millis();
  portfolioLoaded = true;
  Serial.println("Portfolio loaded");
  return true;
}

// ============================================================
// 室內頁
// 400x300 面板配置（無分隔線）：
//  y=22    ：日期 + 星期（6x13）
//  y=138   ：時鐘（62pt，畫面正中央）
//  y=200   ：溫度 + 濕度 + 電量（9x15B）
//  y=270   ：狀態列（6x13）
// ============================================================
void displayIndoor() {
  char buf[64], tmp[32];

  u8g2->clearBuffer();
  u8g2->setDrawColor(1);

  // ── 日期 + 星期 ───────────────────────
  const char *weekdayName[] = {"Sun","Mon","Tue","Wed","Thu","Fri","Sat"};
  struct tm td = {0};
  td.tm_year = ly - 1900;
  td.tm_mon = lmo - 1;
  td.tm_mday = ld;
  td.tm_hour = lh;
  td.tm_min = lm;
  td.tm_sec = ls;
  mktime(&td);
  snprintf(buf, sizeof(buf), "%04d/%02d/%02d  %s",
           ly, lmo, ld, weekdayName[td.tm_wday]);
  u8g2->setFont(u8g2_font_9x15_tf);
  drawCenteredStr(18, buf);

  // ── 時鐘（62pt，畫面正中央）────────
  snprintf(buf, sizeof(buf), "%02d:%02d:%02d", lh, lm, ls);
  u8g2->setFont(u8g2_font_logisoso62_tn);
  drawCenteredStr(138, buf);

  // ── 溫度 + 濕度 + 電量（三合一）──────
  int adcRaw = analogRead(4);
  float batV = adcRaw * 3.3f / 4095.0f * 3.0f;
  float batPct = (batV - 3.0f) / (4.2f - 3.0f) * 100.0f;
  if (batPct < 0) batPct = 0;
  if (batPct > 100) batPct = 100;

  snprintf(buf, sizeof(buf), "%.1f C   %.1f %%   %.2f V",
           lastTemp, lastHum, batV);
  u8g2->setFont(u8g2_font_9x15B_tf);
  drawCenteredStr(200, buf);

  // ── 狀態列 ─────────────────────────────
  u8g2->setFont(u8g2_font_6x13_tf);
  drawCenteredStr(270, lastStatus);

  u8g2->sendBuffer();
}

// ============================================================
void displayPortfolio() {
  char buf[64], tmp[32];

  u8g2->clearBuffer();
  u8g2->setDrawColor(1);
  u8g2->setFont(u8g2_font_6x13_tf);

  // [Portfolio]
  drawCenteredStr(20, "[ Portfolio ]");
  drawHLine(18, 30, 382);

  // ── 總資產 ──────────────────────────────
  u8g2->setFont(u8g2_font_6x13_tf);
  drawCenteredStr(50, "Total Asset");
  u8g2->setFont(u8g2_font_7x13B_tf);
  fmtComma(pf.total_mkt, tmp, sizeof(tmp));
  snprintf(buf, sizeof(buf), "%s TWD", tmp);
  drawCenteredStr(75, buf);
  u8g2->setFont(u8g2_font_6x13_tf);
  fmtComma(pf.total_gain, tmp, sizeof(tmp));
  snprintf(buf, sizeof(buf), "%s (%.1f%%)", tmp, pf.total_gain_pct);
  drawCenteredStr(92, buf);

  // ── 台股 ────────────────────────────────
  drawHLine(18, 107, 382);
  u8g2->setFont(u8g2_font_6x13_tf);
  drawCenteredStr(122, "TW Stocks");
  u8g2->setFont(u8g2_font_7x13B_tf);
  fmtComma(pf.tw_mkt, tmp, sizeof(tmp));
  snprintf(buf, sizeof(buf), "%s TWD", tmp);
  drawCenteredStr(147, buf);
  u8g2->setFont(u8g2_font_6x13_tf);
  fmtComma(pf.tw_gain, tmp, sizeof(tmp));
  snprintf(buf, sizeof(buf), "%s (%.1f%%)", tmp, pf.tw_gain_pct);
  drawCenteredStr(164, buf);

  // ── 美股 ────────────────────────────────
  drawHLine(18, 179, 382);
  u8g2->setFont(u8g2_font_6x13_tf);
  drawCenteredStr(194, "US Stocks");
  u8g2->setFont(u8g2_font_7x13B_tf);
  fmtComma(pf.us_mkt_twd, tmp, sizeof(tmp));
  snprintf(buf, sizeof(buf), "%s TWD", tmp);
  drawCenteredStr(219, buf);
  u8g2->setFont(u8g2_font_6x13_tf);
  fmtComma(pf.us_gain_twd, tmp, sizeof(tmp));
  snprintf(buf, sizeof(buf), "%s (%.1f%%)", tmp, pf.us_gain_pct);
  drawCenteredStr(236, buf);

  // ── 外幣 ────────────────────────────────
  drawHLine(18, 251, 382);
  u8g2->setFont(u8g2_font_6x13_tf);
  fmtComma(pf.usd_amount, tmp, sizeof(tmp));
  snprintf(buf, sizeof(buf), "USD %s @%.3f", tmp, pf.usd_rate);
  drawCenteredStr(268, buf);
  fmtComma(pf.jpy_amount, tmp, sizeof(tmp));
  snprintf(buf, sizeof(buf), "JPY %s @%.4f", tmp, pf.jpy_rate);
  drawCenteredStr(288, buf);

  u8g2->sendBuffer();
}

// ============================================================
void handleKey() {
  static bool lastState = HIGH;
  bool now = digitalRead(KEY_PIN);
  if (now == LOW && lastState == HIGH) {
    if (currentPage == PAGE_INDOOR) {
      currentPage = PAGE_PORTFOLIO;
      unsigned long now = millis();
      if (!portfolioLoaded || (now - pf.lastFetch > PF_REFRESH)) {
        fetchPortfolio();
      }
    } else {
      currentPage = PAGE_INDOOR;
    }
  }
  lastState = now;
}

// ============================================================
void setup() {
  Serial.begin(115200);
  delay(300);

  lcd.begin(0, U8G2_R1);
  u8g2 = lcd.getU8g2();
  Serial.println("LCD OK");

  Wire.begin(13, 14);
  shtc3_wakeup();
  shtc3_soft_reset();
  delay(10);

  pinMode(KEY_PIN, INPUT_PULLUP);

  // ADC 衰減：GPIO4 經分壓器（倍率 3.0）→ 最大 9.9V input
  analogSetAttenuation(ADC_2_5db);  // 0-1.5V range

  float t, h;
  if (shtc3_read(t, h)) {
    lastTemp = t; lastHum = h;
    Serial.printf("SHTC3 OK: %.1fC %.1f%%\n", t, h);
  } else {
    Serial.println("SHTC3 FAILED");
  }

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  bool wifiOk = false;
  for (int i = 0; i < 20; i++) {
    if (WiFi.status() == WL_CONNECTED) { wifiOk = true; break; }
    delay(500);
  }

  if (wifiOk) {
    Serial.println("WiFi OK: " + WiFi.localIP().toString());
    configTime(GMT_OFFSET, 0, NTP_SERVER);
    struct timeval tv;
    tv.tv_sec = 0; tv.tv_usec = 0;
    for (int i = 0; i < 20; i++) {
      gettimeofday(&tv, nullptr);
      if (tv.tv_sec > 1700000000) break;
      delay(500);
    }
    if (tv.tv_sec > 1700000000) {
      struct tm *t = localtime(&tv.tv_sec);
      setRTC(t->tm_hour, t->tm_min, t->tm_sec,
             t->tm_mday, t->tm_mon+1, t->tm_year+1900);
      Serial.println("NTP + RTC OK");
    }
    lastStatus = "WiFi OK";
  } else {
    Serial.println("WiFi FAILED");
    lastStatus = "WiFi OFF";
  }

  fetchPortfolio();
}

// ============================================================
void loop() {
  unsigned long now = millis();

  if (now - lastDisplay >= DISPLAY_MS) {
    if (getRTC(lh, lm, ls, ld, lmo, ly)) {
      if (currentPage == PAGE_INDOOR) displayIndoor();
      else displayPortfolio();
    }
    lastDisplay = now;
  }

  if (now - lastSensor >= SENSOR_MS || lastSensor == 0) {
    float t, h;
    if (shtc3_read(t, h)) { lastTemp = t; lastHum = h; }
    lastSensor = now;
  }

  if (currentPage == PAGE_PORTFOLIO && (now - pf.lastFetch >= PF_REFRESH)) {
    fetchPortfolio();
  }

  if (now - lastKeyCheck >= KEY_MS) {
    handleKey();
    lastKeyCheck = now;
  }

  if ((millis() / 1000) % 16 == 0) delay(1);
  else yield();
}
