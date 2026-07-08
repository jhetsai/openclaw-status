# ESP32 Portfolio 問題分析報告

## 硬體資訊

**Board: ESP32-S3-Touch-LCD-4B (Waveshare)**
- ESP32-S3 X1 (240MHz)
- 4.3" IPS Touch Display (480x272)
- 8MB PSRAM
- 16MB Flash
- USB-C 供電 + 燒錄
- CH340 USB-to-Serial

**韌體燒錄位置：** `/dev/ttyACM0`

---

## 現況（2026-07-07）

### ✅ 已修復並 commit
1. **WiFi Scan 列表空白** — `lvgl_port_lock(10ms → 100ms)` 修復
2. **UpdateUi() watchdog timeout** — 所有 `UpdateUi()` 改為 `update_pending_` flag
3. **WiFi Scan flag 競爭** — `UpdateTimerCallback` 和 `LvglTask` 之間的 `wifi_scan_done_pending_` 競爭已修復
4. **WiFi polling 與 XiaoZhi 衝突** — 改用 `SetNetworkEventCallback`（XiaoZhi WifiStation 統一管理，PortfolioApp 接收事件）
5. **wifi_status_big_label_ null** — 加 null check 並在必要時重建

### ❌ 待修復問題

**P0 - SetNetworkEventCallback 未被呼叫（燒錄中斷）**
- 根本原因：`SetNetworkEventCallback` 從未被執行，導致 WiFi Connected 事件無法 trigger fetch
- 最新燒錄因 esptool 被 SIGKILL 中斷，韌體仍是舊版

---

## 模組化建議（待重構）

### 模組 1：WiFi Manager
- 職責：統一管理 WiFi 連線（目前由 XiaoZhi WifiStation 處理）
- 提供 callback 機制（onConnected, onDisconnected, onGotIP）

### 模組 2：Http Fetcher
- 職責：Fetch URL、JSON parsing、timeout/error handling
- 現有問題：SSL/TLS 憑證設定需修復

### 模組 3：UI Update Manager
- 職責：統一所有 UI 更新透過 flag 機制，LvglTask 負責執行

### 模組 4：Portfolio Display
- 職責：持股資料顯示、天氣顯示、WiFi 設定 UI

---

## 燒錄指令

```bash
ESPTOOL=~/.arduino15/packages/esp32/tools/esptool_py/5.3.0/esptool
BUILD=/home/jhe/.openclaw/workspace/esp32-rlcd-project/02_Example/XiaoZhi/XiaoZhiCode_V2.1.0/build

$ESPTOOL --chip esp32s3 --port /dev/ttyACM0 erase-flash
$ESPTOOL --chip esp32s3 --port /dev/ttyACM0 write-flash \
  0x0 $BUILD/bootloader/bootloader.bin \
  0x8000 $BUILD/partition_table/partition-table.bin \
  0xd000 $BUILD/ota_data_initial.bin \
  0x10000 $BUILD/srmodels/srmodels.bin \
  0x100000 $BUILD/xiaozhi.bin
```

---

## Git Commit 記錄

- `215e567` Add PortfolioDashboard with WiFi event callback integration
- `4c15ccd` Add PortfolioDashboard application (ESP32-S3 LCD 4B)

---

## 測試計畫

### 測試 1：WiFi 連線後自動 fetch
1. 燒錄最新韌體
2. 進 WiFi 設定 → 掃描 → 選 IoT → 輸入密碼
3. 觀察首頁是否顯示 **✅ WiFi OK**
4. 觀察天氣是否出現 actual 度數（不是 --°C）
5. 觀察持股是否顯示 actual 資料（不是 $0）
