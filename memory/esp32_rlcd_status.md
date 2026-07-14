# ESP32-S3-RLCD-4.2 天氣時鐘 - 目前狀態

## 專案路徑
`/home/jhe/.openclaw/workspace/esp32-rlcd-project/02_Example/Arduino/ESP32-S3-RLCD-4.2/`
- 主程式：`ESP32-S3-RLCD-4.2.ino`
- 顯示驅動：`ST7305_U8g2.cpp` / `ST7305_U8g2.h`

## Git
- 無獨立 git repo，程式碼在 Arduino sketch 目錄

## 功能現況

### ✅ 已完成
- 天氣顯示（溫度/濕度/電壓）
- 時鐘顯示（PCF8563 RTC）
- WiFi 自動重連（60秒檢查一次）
- 每 10 分鐘從 R2 下載天氣 JSON
- Telegram Debug 通知

### ❌ 待修 / 待優化
1. **WiFi LCD 狀態圖示** — 需要確認是否正常顯示
2. **編譯失敗** — esp_emote_gfx 與 IDF v5.4.2 不相容（但這是 IDF 版的問題，Arduino 版目前正常）

## 硬體規格
| 項目 | 內容 |
|------|------|
| **LCD** | ST7305 4.2" (400×300) |
| **RTC** | PCF8563 |
| **Framework** | Arduino IDE |
| **WiFi** | SSID: IoT / 密碼: 057851463 |

## 燒錄方式
```bash
# 完整抹除 + 分區燒錄（esptool）
ESPTOOL=~/.arduino15/packages/esp32/tools/esptool_py/5.3.0/esptool
PART=~/.arduino15/packages/esp32/hardware/esp32/3.3.10/tools/partitions
$ESPTOOL --chip esp32s3 --port /dev/ttyACM0 erase-flash
$ESPTOOL --chip esp32s3 --port /dev/ttyACM0 write_flash \
  0x0 $SKETCH/ESP32-S3-RLCD-4.2.ino.bootloader.bin \
  0x8000 $SKETCH/ESP32-S3-RLCD-4.2.ino.partitions.bin \
  0xe000 $PART/boot_app0.bin \
  0x10000 $SKETCH/ESP32-S3-RLCD-4.2.ino.bin
```

## 顯示佈局（400×300）
```
y=22   日期+星期（9x15 font）
y=138  時鐘 62pt（logisoso62_tn）
y=200  溫度+濕度+電壓（9x15B Bold）
y=270  WiFi 狀態（6x13）
y=20   Portfolio 更新時間（右上角，right-aligned）
```

## API URL
- 天氣 JSON：`https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/tmp/weather.json`
- Portfolio JSON：`https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/assets/esp32_portfolio.json`
- Telegram Bot：`879343...ER8A`

## 關鍵修正記錄
- `lcd.begin(0, U8G2_R1)` → `lcd.begin(1, U8G2_R0)` — 解決記憶體不足（273KB → 91KB）
- ESP32-S3 內建溫度感測器不相容，改用天氣 API 溫度
- JSON `"updated": "..."`（冒號後有空格）解析錯誤 → 已修正

## 下一步
1. 確認 WiFi LCD 狀態圖示是否正常
2. 評估是否要加入 Touch 輸入
