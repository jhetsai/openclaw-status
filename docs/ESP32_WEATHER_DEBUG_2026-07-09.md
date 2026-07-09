# ESP32 天氣描述問題 — 搶救計畫
> 建立：2026-07-09 | 更新：2026-07-09

---

## 🔍 問題症狀

**螢幕上：**
- WiFi 狀態：✅ 顯示正常（SSID + dB）
- 溫度：✅ 顯示正常（33°C）
- 天氣描述：❌ 空白
- 更新時間：❌ 空白
- NTP 時鐘：❌ 無法對時（程式碼未燒入）

**序列輸出：**
- `I (xxx) PortfolioApp: PortfolioApp running...` 每 10 秒一次 ✅
- Watchdog 警告每 ~60 秒一次（不影響運行，純警告）

---

## 🐛 根本原因

### Bug 1：strncpy offset 錯誤（已修正，未燒錄驗證）

JSON 格式（扁平化後）：
```
{"time":"2026-07-09 16:00:03","temp":33,"desc":"Patchy rain nearby","humidity":80,"updated":1783584003}
```

C 程式（錯誤）：
```cpp
p = strstr(flat, "\"desc\": \"");        // ✅ 找得到，p 指向 "
strncpy(weather_.desc, p + 8, ...);     // ❌ p+8 指向開頭 "，不是內容
char *end = strstr(weather_.desc, "\""); // ❌ 永遠找不到第二個 "
```

正確應該是 `p + 9`（跳過 `"desc": "` 8 字元再多跳一個空格）。

**修正後：**
```cpp
p = strstr(flat, "\"desc\": \"");        // ✅ 找 "desc": "
strncpy(weather_.desc, p + 9, ...);     // ✅ p+9 指向 P
char *end = strstr(weather_.desc, "\""); // ✅ 找得到結尾的 "
if (end) *end = '\0';
```

同樣問題在 `time`/`updated` 欄位：`p + 8` → `p + 9`

---

### Bug 2：Pattern 有多餘空格（已修正）

```cpp
// 錯誤（JSON 是 "temp":33，: 後無空格）
strstr(flat, "\"temp\": ");      // 找不到！
sscanf(p, "\"temp\": %f", ...); // 多了一個空格

// 正確
strstr(flat, "\"temp\":");       // ✅
sscanf(p, "\"temp\":%f", ...);   // ✅
```

---

## 📁 關鍵檔案

| 檔案 | 用途 |
|------|------|
| `esp32-rlcd-project/02_Example/ESP32-S3-Touch-LCD-4.3B/main/application_portfolio.cc` | 主要程式碼 |
| `esp32-rlcd-project/02_Example/ESP32-S3-Touch-LCD-4.3B/sdkconfig` | Watchdog 60 秒設定 |
| `esp32-rlcd-project/02_Example/ESP32-S3-Touch-LCD-4.3B/sdkconfig.defaults.esp32s3` | 預設編譯設定 |

---

## 🔧 繼續搶救步驟

### Step 1：燒錄最新版本

```bash
cd /home/jhe/.openclaw/workspace/esp32-rlcd-project/02_Example/ESP32-S3-Touch-LCD-4.3B
. /home/jhe/esp-idf-v5.4.2/export.sh >/dev/null 2>&1
idf.py -p /dev/ttyACM0 flash
```

燒錄完等待 10 秒。

### Step 2：監控序列輸出

```bash
python3 << 'PYEOF'
import serial, time
ser = serial.Serial('/dev/ttyACM1', 115200, timeout=8)
time.sleep(3)
ser.flushInput()
for i in range(60):
    if ser.in_waiting > 0:
        data = ser.read(ser.in_waiting)
        print(data.decode('utf-8', errors='replace'))
    time.sleep(0.5)
ser.close()
PYEOF
```

**預期看到的關鍵 LOG：**
```
I (xxx) [NET] WiFi Connected to IoT           ← WiFi 連線
I (xxx) Weather JSON: {"time":"2026-07-09...   ← FetchWeather 成功
I (xxx) [DEBUG] ParseWeather: temp=33 desc=[Patchy rain nearby] humidity=80 updated=[2026-07-09 16:00:03]
I (xxx) [NTP] SNTP 啟動 (tw.pool.ntp.org)     ← NTP 啟動
```

### Step 3：檢查螢幕
- 天氣描述（33°C 右邊那欄）是否出現 `Patchy rain nearby`？
- 更新時間（濕度右邊）是否出現 `16:00:03`？
- 時鐘是否正確（每分鐘比對）？

### Step 4：若天氣描述仍是空白
檢查 `WiFi Connected` callback 有沒有被呼叫：
- 序列中是否有 `[NET] WiFi Connected`？
- 若沒有 → WiFi callback 沒觸發，檢查 `SetNetworkEventCallback` 設定

---

## ⚠️ Watchdog 警告說明

```
E (xxx) task_wdt: Task watchdog got triggered
E (xxx)  - IDLE1 (CPU 1)
E (xxx) CPU 1: LvglTask
```

**不是當機**，是 LVGL render 佔滿 CPU1，導致 IDLE1 任務沒有機會重置 watchdog。
`CONFIG_ESP_TASK_WDT_TIMEOUT_S=60` 已設定（從 20s 改 60s）。

backtrace 顯示：
- `lv_refr.c:277` — LVGL 畫面刷新
- `lv_obj_pos.c:847` — 物件位置計算
- `lv_label.c:1209` — 標籤渲染

---

## 📋 程式碼修改摘要（相對於 XiaoZhiCode_V2.1.0）

### 1. WiFi Connected Callback（NTP 已加入）
位置：`application_portfolio.cc` ~line 129
```cpp
this->FetchPortfolio();
this->FetchWeather();

static bool sntp_init_done = false;
if (!sntp_init_done) {
    sntp_init_done = true;
    setenv("TZ", "CST-8", 1);
    tzset();
    esp_sntp_config_t cfg = {
        .smooth_sync = true,
        .server_from_dhcp = false,
        .wait_for_sync = false,
        .start = true,
        .num_of_servers = 1,
        .servers = {"tw.pool.ntp.org", NULL, NULL}
    };
    esp_netif_sntp_init(&cfg);
    ESP_LOGI(TAG, "[NTP] SNTP 啟動 (tw.pool.ntp.org)");
}
```

### 2. ParseWeatherJson 修正（desc/updated offset）
位置：`application_portfolio.cc` ~line 508-540
- `strstr(flat, "\"desc\": \"")` — ✅ 找得到
- `strncpy(..., p + 9, ...)` — ✅ 正確 offset
- `strstr(flat, "\"time\": \"")` — ✅ 有空格
- `strncpy(..., p + 9, ...)` — ✅ 正確 offset
- DEBUG LOG 已加入

### 3. sdkconfig
- `CONFIG_ESP_TASK_WDT_TIMEOUT_S=60`
- `CONFIG_LWIP_SNTP_MAX_SERVERS=3`

---

## 📌 未解決項目

1. **天氣描述/更新時間** — 已修正但未燒錄驗證
2. **NTP 網路對時** — 已加入程式碼但未燒錄驗證
3. **Watchdog 警告** — 已知問題，不影響運行，可接受

---

## 🔑 燒錄/監控捷徑

```bash
# 燒錄
idf.py -p /dev/ttyACM0 flash

# 監控（燒完後開新視窗）
idf.py -p /dev/ttyACM1 monitor
# 或
python3 -c "
import serial
s=serial.Serial('/dev/ttyACM1',115200,timeout=5)
s.flushInput()
for _ in range(30):
    if s.in_waiting: print(s.read(s.in_waiting).decode('utf-8',errors='replace'))
    import time; time.sleep(0.5)
"
```
