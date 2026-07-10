# ESP32-S3-Touch-LCD-4.3B Portfolio App 專案摘要

> 最後更新：2026-07-10 | 韌體版本：2.1.0

---

## 基本資訊

| 項目 | 內容 |
|------|------|
| **硬體** | ESP32-S3-Touch-LCD-4B (Waveshare) 4.3" IPS Touch (480x480) |
| **Framework** | ESP-IDF v5.4.2 |
| **Board** | WAVESHARE_S3_TOUCH_LCD_4B |
| **WiFi** | SSID: `IoT` / 密碼: `057851463` |
| **燒錄位置** | `/dev/ttyACM0` |
| **韌體版本** | `2.1.0` |

---

## 程式碼位置

| 用途 | 路徑 |
|------|------|
| **主程式** | `esp32-rlcd-project/02_Example/ESP32-S3-Touch-LCD-4.3B/` |
| **核心原始碼** | `main/application_portfolio.cc` / `.h` |
| **專案模組 Git** | `esp32-rlcd-project/.git/`（submodule）|

---

## Git 版本對照

| 層級 | Commit | 說明 |
|------|--------|------|
| **Workspace Git** | `8c1fed0` | 備份 + 日誌收錄（2026-07-10） |
| **ESP32 專案 Git** | `756daa7a` | 時鐘重構 commit |

```bash
# Workspace repo
cd /home/jhe/.openclaw/workspace
git log --oneline -1  # → 8c1fed0

# ESP32 專案 repo
cd /home/jhe/.openclaw/workspace/esp32-rlcd-project/02_Example/ESP32-S3-Touch-LCD-4.3B
git log --oneline -1  # → 756daa7a
```

---

## 韌體備份（2026-07-10）

**位置：** `/home/jhe/.openclaw/workspace/backups/2026-07-10/`

| 檔案 | 說明 |
|------|------|
| `xiaozhi_2026-07-10_1534.bin` | 主韌體（4.3MB）|
| `partition-table_2026-07-10.bin` | 分區表 |
| `bootloader_2026-07-10.bin` | Bootloader |
| `application_portfolio.cc` | 原始碼（含本次維修）|
| `application_portfolio.h` | Header |
| `memory_2026-07-10.md` | 詳細維修日誌 |
| `README.md` | 還原燒錄說明 |

---

## 顯示佈局（480×480 面板）

```
y=0, h=45   Header（蝦助攻客 | WiFi | 12:34）
y=50, h=80  天氣卡片（滿版寬度）
y=135        持股 + 現金 + 匯率（2×2 網格）
  左(8,135)     持股卡片（232×290）← 左側滿高度
  右上(248,135) 現金卡片（224×140）← 右側上半
  右下(248,283) 匯率卡片（224×142）← 右側下半
```

---

## 燒錄流程

```bash
PROJ=/home/jhe/.openclaw/workspace/esp32-rlcd-project/02_Example/ESP32-S3-Touch-LCD-4.3B
BACKUP=/home/jhe/.openclaw/workspace/backups/2026-07-10
. ~/esp-idf-v5.4.2/export.sh

# 方式一：從 source rebuild（推薦，需修改時）
idf.py build
idf.py -p /dev/ttyACM0 erase-flash
idf.py -p /dev/ttyACM0 flash

# 方式二：直接燒 bin（快速，還原時）
ESPTOOL=~/.arduino15/packages/esp32/tools/esptool_py/5.3.0/esptool
$ESPTOOL --chip esp32s3 --port /dev/ttyACM0 erase-flash
$ESPTOOL --chip esp32s3 --port /dev/ttyACM0 write_flash 0x1000 $BACKUP/bootloader_2026-07-10.bin
$ESPTOOL --chip esp32s3 --port /dev/ttyACM0 write_flash 0x8000 $BACKUP/partition-table_2026-07-10.bin
$ESPTOOL --chip esp32s3 --port /dev/ttyACM0 write_flash 0x10000 $BACKUP/xiaozhi_2026-07-10_1534.bin
```

**燒完後按 RST 確認開機 log。**

---

## 2026-07-10 維修記錄

### 問題與修復

| 問題 | 原因 | 修復方式 |
|------|------|---------|
| 時鐘秒數落後 3 秒 | `esp_timer` + `lvgl_port_lock` 竞争 | 改用 `lv_timer_create()`（LVGL 內部 lock-safe）|
| WiFi 連線後時鐘亂跳 | SNTP init 太晚，`clock_base_time_` 被錯誤更新 | `Initialize()` 直接 init SNTP，不等 WiFi callback |
| NTP sync 延遲 | WiFi 連線慢，SNTP 還沒 sync | 每 10 秒用 `time()` Fallback |
| WiFi RSSI fetch 失敗 | WiFi callback 在 sys_evt stack（太小），TLS 爆 | WiFi callback 只設 flag，RSSI fetch 移到 LvglTask |

### 時鐘公式

```cpp
time_t now = (clock_base_time_ > 1000000000L)
    ? clock_base_time_ + clock_seconds_   // SNTP sync 後
    : time(nullptr);                      // Fallback：直接用系統時間
```

### Timer 架構

| 用途 | 方法 | 說明 |
|------|------|------|
| 時鐘（1Hz）| `lv_timer_create()` | LVGL task 內執行，自帶 lock-safe |
| 資料更新（1分鐘）| `esp_timer_start_periodic()` | 獨立運行，不阻塞 UI |

### WiFi RSSI 更新時序

```
WiFi Connected → wifi_just_connected_=true → LvglTask fetch RSSI → 更新 UI
```

---

## 重要修改（每次重燒需確認）

1. `sdkconfig`：`CONFIG_BOARD_TYPE_WAVESHARE_S3_TOUCH_LCD_4B=y`
2. `esp32-s3-touch-lcd-4b.cc`：GT911 touch init struct 修正
3. `esp_emote_gfx CMakeLists.txt`：加 `-Wno-error=format`

---

## 已知問題

| 問題 | 狀態 | 說明 |
|------|------|------|
| USB 燒錄後 ESP32 不自動重置 | ⚠️ 已知 | 需要手動按 RST |
| deep sleep mode 導致 USB 斷開 | ⚠️ 已知 | 按 RST 喚醒 |
| ESP32-S3 內建溫度感測器不相容 | ⚠️ 已知 | 用天氣 API 溫度代替 |
