# 太陽能發電監控系統架設教學
## ESP32 + INA219 功率計

---

# 1. 材料清單

## 1.1 硬體材料

| 項目 | 規格 | 參考費用 | 備註 |
|------|------|---------|------|
| ESP32 主機板 | ESP32 DevKit v1 | NT$150-250 | 需有 WiFi 功能 |
| INA219 功率模組 | I2C 介面 | NT$30-80 | 可測電壓/電流/功率 |
|  shunt 電阻 | 0.1Ω 2W | 已附在 INA219 模組 | 用於電流檢測 |
| 連接線 | Dupont 線 10cm | NT$30 | 公的/母的各一些 |
| 麵包板 | 400孔 | NT$50 | 方便臨時測試 |
| USB 電源 | 5V 2A | 家裡已有 | 供電給 ESP32 |

## 1.2 可選材料

| 項目 | 用途 | 費用 |
|------|------|------|
| OLED 顯示器 | 1306 I2C 0.96" | NT$100 |
| 18650 鋰電池 | 3.7V 3000mAh | NT$50 |
| 鋰電池模組 | TP4056 充電板 | NT$30 |

---

# 2. INA219 模組介紹

## 2.1 腳位說明

```
+-------------------+
|  INA219 Module    |
+-------------------+
| VCC (+)           | → 3.3V (ESP32)
| GND (-)           | → GND (ESP32)
| SCL               | → GPIO 22 (ESP32)
| SDA               | → GPIO 21 (ESP32)
| V+ (Vin+)         | → 太陽能正極
| V- (Vin-)         | → 太陽能負極（經過 shunt）
+-------------------+
```

## 2.2 電路接線圖

```
太陽能板 (+) ──────────┬─────────────── 負載 ────────── 蓄電池 (+)
                       │                                    │
                       │                                    │
                     [INA219]                              │
                      V+  V-                                │
                       │   │                                │
                       │   └──[0.1Ω Shunt]──┘            │
                       │                                    │
                       │                                    │
                      GND ──────────────────────────────── 蓄電池 (-)
```

## 2.3 簡化接線（推薦）

```
太陽能控制器 → 蓄電池
      │
      ├──→ INA219 V+ (太陽能正極輸入)
      │
      ├──→ INA219 V- (太陽能正極輸出，去電池)
      │
      └──→ ESP32 GND (共地)
      
ESP32 → INA219:
  3.3V → VCC
  GND → GND
  GPIO 22 → SCL
  GPIO 21 → SDA
```

---

# 3. Arduino IDE 設定

## 3.1 安裝 ESP32 開發板

1. 開啟 Arduino IDE
2. 進入「檔案」→「偏好設定」
3. 在「額外的開發板管理員網址」加入：
   ```
   https://dl.espressif.com/dl/package_esp32_index.json
   ```
4. 進入「工具」→「開發板」→「開發板管理員」
5. 搜尋「ESP32」並安裝

## 3.2 安裝 INA219 函式庫

1. 進入「草稿碼」→「 Include Library」→「Manage Libraries」
2. 搜尋「Adafruit INA219」並安裝
3. 搜尋「Adafruit BusIO」並安裝（如果需要）
4. 搜尋「ESPAsyncTCP」並安裝（WiFi 用）

---

# 4. 程式碼

## 4.1 完整程式碼（ESP32_Solar_Monitor.ino）

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_INA219.h>

// ============ 設定區 ============

// WiFi 設定
const char* WIFI_SSID = "你的WiFi名稱";
const char* WIFI_PASS = "你的WiFi密碼";

// API 伺服器設定
const char* API_HOST = "http://你的伺服器IP:3838";
const char* API_KEY = "optional_api_key";

// INA219 設定
#define INA219_ADDRESS 0x40  // 預設 I2C 位址

// 更新間隔（毫秒）
const long UPDATE_INTERVAL = 60000;  // 1分鐘

// ============ 物件 ============

Adafruit_INA219 ina219;
HTTPClient http;

// ============ 函式 ============

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("太陽能發電監控系統啟動中...");
  
  // 初始化 INA219
  if (!ina219.begin()) {
    Serial.println("INA219 初始化失敗！");
    while(1) { delay(10); }
  }
  Serial.println("INA219 初始化成功");
  
  // 設定 INA219 範圍
  ina219.setCalibration_32V_2A();  // 適用於 200W 太陽能板
  
  // 連接 WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("連接 WiFi...");
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi 連接成功！");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi 連接失敗！");
  }
}

void loop() {
  // 讀取 INA219 資料
  float shuntvoltage = ina219.getShuntVoltage_mV();
  float busvoltage = ina219.getBusVoltage_V();
  float current_mA = ina219.getCurrent_mA();
  float power_mW = ina219.getPower_mW();
  float voltage_V = busvoltage + (shuntvoltage / 1000);
  
  // 計算發電量（累計）
  static float totalEnergy_Wh = 0;
  static unsigned long lastTime = 0;
  
  unsigned long now = millis();
  if (lastTime > 0) {
    float hours = (now - lastTime) / 3600000.0;
    totalEnergy_Wh += (power_mW / 1000.0) * hours;
  }
  lastTime = now;
  
  // 顯示在 Serial Monitor
  Serial.println("========== 發電資料 ==========");
  Serial.print("電壓: "); Serial.print(voltage_V, 2); Serial.println(" V");
  Serial.print("電流: "); Serial.print(current_mA, 0); Serial.println(" mA");
  Serial.print("功率: "); Serial.print(power_mW, 0); Serial.println(" mW");
  Serial.print("累計發電: "); Serial.print(totalEnergy_Wh, 3); Serial.println(" Wh");
  Serial.println("================================");
  
  // 上傳到伺服器
  if (WiFi.status() == WL_CONNECTED) {
    sendToServer(voltage_V, current_mA, power_mW, totalEnergy_Wh);
  }
  
  delay(UPDATE_INTERVAL);
}

void sendToServer(float voltage, float current, float power, float energy) {
  HTTPClient http;
  String url = String(API_HOST) + "/api/solar";
  url += "?voltage=" + String(voltage, 2);
  url += "&current=" + String(current, 1);
  url += "&power=" + String(power, 1);
  url += "&energy=" + String(energy, 3);
  
  http.begin(url);
  int httpCode = http.GET();
  
  if (httpCode == 200) {
    Serial.println("上傳成功！");
  } else {
    Serial.print("上傳失敗，HTTP Code: ");
    Serial.println(httpCode);
  }
  
  http.end();
}
```

## 4.2 system-api 新增端點

在 `/home/jhe/system-api/server.js` 加入：

```javascript
// 太陽能資料（記憶體）
let solarData = {
  voltage: 0,
  current: 0,
  power: 0,
  energy: 0,
  timestamp: null
};

// 太陽能 API 端點
if (req.method === 'GET' && req.url.startsWith('/api/solar')) {
  // 解析參數
  const params = new URL(req.url, 'http://localhost').searchParams;
  solarData = {
    voltage: parseFloat(params.get('voltage')) || 0,
    current: parseFloat(params.get('current')) || 0,
    power: parseFloat(params.get('power')) || 0,
    energy: parseFloat(params.get('energy')) || 0,
    timestamp: new Date().toISOString()
  };
  res.end(JSON.stringify({status: 'ok'}));
}
```

---

# 5. 電路接線詳細圖

## 5.1 完整接線圖（文字版）

```
                    USB 5V
                       │
                       ▼
               ┌───────────────┐
               │    ESP32     │
               │  DevKit v1   │
               └───────────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
        GND           D22           D21
         │           (SCL)         (SDA)
         │             │             │
         └─────────────┴─────────────┘
                       │
                   ┌───┴───┐
                   │ INA219│
                   └───┬───┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
        GND           VCC           V+
         │           (3.3V)           │
         │             │             │
         └─────────────┘             │
                                     │
        太陽能輸入 ──[0.1Ω]──┤
                              │
                            V-
```

## 5.2 INA219 模組放大圖

```
    ┌─────────────┐
    │   INA219    │
    │  Module     │
────┤ VCC     SCL ├──── D22 (ESP32)
────┤ GND     SDA ├──── D21 (ESP32)
────┤ V+      ADDR│
────┤ V-         ├──── (不接)
    └─────────────┘
```

---

# 6. 測試與校正

## 6.1 測試 INA219

上傳這個測試程式碼：

```cpp
#include <Wire.h>
#include <Adafruit_INA219.h>

Adafruit_INA219 ina219;

void setup() {
  Serial.begin(115200);
  if (!ina219.begin()) {
    Serial.println("INA219 未找到！");
    while(1);
  }
}

void loop() {
  Serial.print("電壓: "); Serial.print(ina219.getBusVoltage_V(), 2); Serial.println(" V");
  Serial.print("電流: "); Serial.print(ina219.getCurrent_mA(), 0); Serial.println(" mA");
  Serial.print("功率: "); Serial.print(ina219.getPower_mW(), 0); Serial.println(" mW");
  delay(1000);
}
```

## 6.2 校正電流值

INA219 預設 shunt 電阻是 0.1Ω，如果你的不同，需要調整：

```cpp
// 假設你的 shunt 是 0.05Ω (50mΩ)
ina219.setCalibration_32V_1A();  // 或自訂：
ina219.setCalibration(0.05, 0.1);  // shuntOhms, mA_Per_LSB
```

---

# 7. 進階功能

## 7.1 加入 OLED 顯示器

```cpp
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

void setup() {
  // 初始化 OLED
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED 初始化失敗");
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
}

void showOLED(float v, float w) {
  display.clearDisplay();
  display.setCursor(0,0);
  display.println("☀️ 太陽能發電");
  display.print("電壓: "); display.print(v, 1); display.println(" V");
  display.print("功率: "); display.print(w, 0); display.println(" W");
  display.display();
}
```

## 7.2 太陽能效率計算

```cpp
// 假設 200W 面板
#define PANEL_WATT 200.0

float efficiency = (power_mW / 1000.0 / PANEL_WATT) * 100;
Serial.print("發電效率: ");
Serial.print(efficiency, 1);
Serial.println(" %");
```

## 7.3 異常警報

```cpp
void checkAlert() {
  if (voltage_V < 10.0) {
    Serial.println("⚠️ 電壓過低！檢查太陽能板連接");
  }
  if (power_mW < 100 && voltage_V > 20) {
    Serial.println("⚠️ 有電壓但無發電，可能太陽能板問題");
  }
  if (isnan(current_mA)) {
    Serial.println("⚠️ INA219 讀取錯誤");
  }
}
```

---

# 8. 故障排除

## 8.1 INA219 讀不到

1. 檢查 I2C 接線（SCL/SDA）
2. 確認 VCC 是 3.3V 不是 5V
3. 確認 GND 共地
4. 用 I2C Scanner 確認位址：

```cpp
#include <Wire.h>
void setup() {
  Wire.begin();
  Serial.begin(115200);
  for (byte address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    if (Wire.endTransmission() == 0) {
      Serial.print("I2C 設備找到: 0x");
      Serial.println(address, HEX);
    }
  }
}
```

## 8.2 WiFi 連不上

1. 確認 SSID 和密碼正確
2. 確認 WiFi 是 2.4GHz（ESP32 不支援 5GHz）
3. 檢查路由器設定

## 8.3 電流值異常

1. 檢查 shunt 電阻是否正確
2. 確認 INA219 校正設定正確
3. 確認範圍設定（32V_2A 或 32V_1A）

---

# 9. 整合到系統狀態頁面

## 9.1 修改 system-api

在 `/home/jhe/system-api/server.js` 加入：

```javascript
} else if (req.method === 'GET' && req.url === '/api/solar') {
    res.end(JSON.stringify(solarData));
}
```

## 9.2 更新 HTML

在系統狀態頁面加入：

```html
<details>
    <summary>☀️ 太陽能發電（即時）</summary>
    <div id="solar-data">
        <p>電壓: <span id="s-v">--</span> V</p>
        <p>電流: <span id="s-c">--</span> mA</p>
        <p>功率: <span id="s-p">--</span> W</p>
        <p>累計: <span id="s-e">--</span> kWh</p>
    </div>
</details>

<script>
async function updateSolar() {
    try {
        const r = await fetch('http://你的伺服器:3838/api/solar');
        const d = await r.json();
        document.getElementById('s-v').textContent = d.voltage?.toFixed(1) || '--';
        document.getElementById('s-c').textContent = (d.current/1000)?.toFixed(2) || '--';
        document.getElementById('s-p').textContent = (d.power/1000)?.toFixed(2) || '--';
        document.getElementById('s-e').textContent = (d.energy/1000)?.toFixed(3) || '--';
    } catch(e) { console.log('Solar data unavailable'); }
}
setInterval(updateSolar, 5000);
updateSolar();
</script>
```

---

# 10. 費用預估

| 項目 | NT$ |
|------|-----|
| ESP32 DevKit v1 | 150 |
| INA219 模組 | 50 |
| Dupont 線材 | 30 |
| 麵包板 | 50 |
| OLED 顯示器（可選） | 100 |
| **基本款合計** | **~280** |
| **進階款（含 OLED）** | **~380** |

---

# 11. 參考資源

- Adafruit INA219 Library: https://github.com/adafruit/Adafruit_INA219
- ESP32 Arduino Docs: https://docs.espressif.com/projects/arduino-esp32/
- INA219 Datasheet: https://www.ti.com/lit/ds/symlink/ina219.pdf

---

_本文件由蝦助生成_
_2026-04-07_
