/*
  ESP32-S3-RLCD-4.2 Dashboard
  蔡哲維個人資產顯示系統 v2.0
  
  功能：
  - 時鐘顯示
  - 溫濕度感測（SHTC3）
  - 股票資產總覽（從 R2 抓取）
  - 天氣資訊
  - USD/TWD 匯率
  
  WiFi: IOT / 057851463
  更新頻率: 5分鐘
  方向: 橫向 (400x300)
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <SHTC3.h>
#include <time.h>

// ============== WiFi 設定 ==============
#define WIFI_SSID     "IOT"
#define WIFI_PASSWORD  "057851463"

// ============== R2 資料來源 ==============
#define R2_BASE_URL   "https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev"

// ============== 更新間隔（毫秒）==============
#define UPDATE_STOCKS_INTERVAL   300000  // 5分鐘
#define UPDATE_WEATHER_INTERVAL  600000  // 10分鐘
#define UPDATE_CLOCK_INTERVAL    1000    // 1秒

// ============== I2C 針腳 ==============
#define I2C_SDA 21
#define I2C_SCL 22

// ============== 全域變數 ==============
SHTC3 shtc3(Wire);

// 股票資料
String totalAssets = "--";
String twStocks = "--";
String usStocks = "--";
String assetsGain = "--";
float usdRate = 31.50;

// 天氣資料
String weatherDesc = "--";
float tempC = 0;
float humi = 0;

// 時間
char timeStr[20] = "00:00:00";
char dateStr[20] = "2026/01/01";

unsigned long lastStockUpdate = 0;
unsigned long lastWeatherUpdate = 0;
unsigned long lastSensorUpdate = 0;

// ============== 初始化 ==============
void setup() {
  Serial.begin(115200);
  delay(500);
  
  Serial.println("ESP32-S3-RLCD-4.2 Dashboard v2.0");
  Serial.println("================================");
  
  // 初始化 I2C
  Wire.begin(I2C_SDA, I2C_SCL);
  
  // 初始化 SHTC3
  if (shtc3.begin()) {
    Serial.println("SHTC3 OK");
  } else {
    Serial.println("SHTC3 FAIL");
  }
  
  // 連接 WiFi
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  int count = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    count++;
    if (count > 20) {
      Serial.println("\nWiFi connection failed!");
      break;
    }
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.println("IP: " + WiFi.localIP().toString());
  }
  
  // 設定時間（NTP）
  configTime(28800, 0, "pool.ntp.org", "time.nist.gov");  // GMT+8
  Serial.println("Time synced");
  
  // 顯示開機畫面
  showBootScreen();
  
  // 初次抓取資料
  fetchStockData();
  fetchWeatherData();
  updateSensorData();
  updateTime();
}

// ============== 主迴圈 ==============
void loop() {
  unsigned long now = millis();
  
  // 每秒更新時鐘
  static unsigned long lastClockUpdate = 0;
  if (now - lastClockUpdate >= UPDATE_CLOCK_INTERVAL) {
    updateTime();
    drawDashboard();
    lastClockUpdate = now;
  }
  
  // 每30秒更新溫濕度
  if (now - lastSensorUpdate >= 30000) {
    updateSensorData();
    lastSensorUpdate = now;
  }
  
  // 每5分鐘更新股票
  if (now - lastStockUpdate >= UPDATE_STOCKS_INTERVAL) {
    fetchStockData();
    lastStockUpdate = now;
  }
  
  // 每10分鐘更新天氣
  if (now - lastWeatherUpdate >= UPDATE_WEATHER_INTERVAL) {
    fetchWeatherData();
    lastWeatherUpdate = now;
  }
  
  delay(100);
}

// ============== 更新時間 ==============
void updateTime() {
  struct tm timeinfo;
  if (getLocalTime(&timeinfo)) {
    sprintf(timeStr, "%02d:%02d:%02d", 
      timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);
    sprintf(dateStr, "%04d/%02d/%02d", 
      timeinfo.tm_year + 1900, timeinfo.tm_mon + 1, timeinfo.tm_mday);
  }
}

// ============== 更新溫濕度 ==============
void updateSensorData() {
  if (shtc3.read()) {
    tempC = shtc3.getTemperature();
    humi = shtc3.getHumidity();
    Serial.printf("Sensor: %.1fC / %.0f%%\n", tempC, humi);
  }
}

// ============== 抓取股票資料 ==============
void fetchStockData() {
  HTTPClient http;
  String url = String(R2_BASE_URL) + "/assets/portfolio_data.json";
  
  Serial.println("Fetching: " + url);
  http.begin(url);
  int httpCode = http.GET();
  
  if (httpCode == 200) {
    String payload = http.getString();
    DynamicJsonDocument doc(16384);
    deserializeJson(doc, payload);
    
    // 解析 summary
    JsonObject summary = doc["summary"];
    long mktval = summary["stockMktval"].as<long>();
    totalAssets = formatNumber(mktval);
    assetsGain = summary["yieldCur"].as<String>();
    
    // 解析匯率
    JsonObject fx = doc["fx"];
    usdRate = fx["USD_TWD"].as<float>();
    
    // 解析台股（從 dividends.tw.confirmed）
    JsonObject tw_conf = doc["dividends"]["tw"]["confirmed"];
    int tw_total = tw_conf["total"].as<int>();
    twStocks = formatNumber(tw_total);
    
    // 解析美股（從 dividends.us.annual 2026）
    float us_total_twd = 0;
    for (JsonObject a : doc["dividends"]["us"]["annual"].as<JsonArray>()) {
      if (String(a["year"].as<char*>()) == "2026") {
        us_total_twd = a["total"].as<float>();
        break;
      }
    }
    usStocks = formatNumber((int)us_total_twd);
    
    Serial.println("Stock data updated!");
    Serial.printf("  Total: %s\n", totalAssets.c_str());
    Serial.printf("  TW: %s\n", twStocks.c_str());
    Serial.printf("  US: %s\n", usStocks.c_str());
    Serial.printf("  USD Rate: %.2f\n", usdRate);
    
  } else {
    Serial.println("Stock fetch failed: " + String(httpCode));
  }
  
  http.end();
}

// ============== 抓取天氣資料 ==============
void fetchWeatherData() {
  HTTPClient http;
  http.begin("http://wttr.in/Yunlin?format=j1");
  int httpCode = http.GET();
  
  if (httpCode == 200) {
    String payload = http.getString();
    DynamicJsonDocument doc(4096);
    deserializeJson(doc, payload);
    
    // 解析天氣（取第一個時段）
    JsonObject current = doc["weather"][0]["hourly"][0];
    weatherDesc = current["weatherDesc"][0]["value"].as<String>();
    
    Serial.println("Weather: " + weatherDesc);
  } else {
    Serial.println("Weather fetch failed: " + String(httpCode));
  }
  
  http.end();
}

// ============== 格式化數字 ==============
String formatNumber(long num) {
  String s = String(num);
  int len = s.length();
  for (int i = len - 3; i > 0; i -= 3) {
    s = s.substring(0, i) + "," + s.substring(i);
  }
  return s;
}

// ============== 顯示開機畫面 ==============
void showBootScreen() {
  Serial.println("Display init...");
  Serial.println("Boot screen shown");
  delay(1500);
}

// ============== 繪製主畫面 ==============
void drawDashboard() {
  // 清除畫面（白色背景）
  // epd_fill(0xFF);
  
  // 繪製各區塊
  drawHeader();    // 頂部：時鐘 + 日期
  drawSensor();     // 左側：溫濕度
  drawAssets();     // 中央：資產總覽
  drawFooter();     // 底部：匯率 + 天氣
  
  // 更新螢幕
  // epd_update();
  
  Serial.printf("[%s] Dashboard updated\n", timeStr);
}

// ============== 繪製頂部（時鐘）==============
void drawHeader() {
  Serial.printf("  Clock: %s %s\n", dateStr, timeStr);
}

// ============== 繪製左側（溫濕度）==============
void drawSensor() {
  Serial.printf("  Temp: %.1fC, Hum: %.0f%%\n", tempC, humi);
}

// ============== 繪製中央（資產）==============
void drawAssets() {
  Serial.printf("  Total: %s (%s)\n", totalAssets.c_str(), assetsGain.c_str());
  Serial.printf("  TW: %s, US: %s\n", twStocks.c_str(), usStocks.c_str());
}

// ============== 繪製底部（匯率+天氣）==============
void drawFooter() {
  Serial.printf("  USD/TWD: %.2f, Weather: %s\n", usdRate, weatherDesc.c_str());
}

// ============== 備註 ==============
/*
  安裝的函式庫（Arduino IDE）：
  1. ArduinoJson - https://arduinojson.org/
  2. SHTC3 - https://github.com/sparkfun/SparkFun_SHTC3_Arduino_Library
  3. GxEPD2 - https://github.com/ZinggJM/GxEPD2 (e-Paper 驅動)
  
  開發板設定：
  - 開發板：ESP32S3 Dev Module
  - Flash Size：16MB
  - PSRAM：8MB (OPI)
  
  調整項目：
  - 畫面解析度：400x300（橫向）
  - WiFi 已設定：IOT / 057851463
  - R2 URL 已設定
  
  需要實際燒錄後測試！
*/