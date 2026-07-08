# XiaoZhi ESP32-S3-Touch-LCD-4B 備份（2026-07-01 修正版）

## 包含的修改

### 1. sdkconfig - Board Type 修正
- 將 `CONFIG_BOARD_TYPE_BREAD_COMPACT_WIFI=y` 註解掉
- 開啟 `CONFIG_BOARD_TYPE_WAVESHARE_S3_TOUCH_LCD_4B=y`

### 2. esp32-s3-touch-lcd-4b.cc - GT911 I2C struct 修正
- 位置：`main/boards/waveshare-s3-touch-lcd-4b/esp32-s3-touch-lcd-4b.cc`
- 將 `ESP_LCD_TOUCH_IO_I2C_GT911_CONFIG()` 巨集替換為手動 struct 初始化
- 因為 ESP-IDF v5.4.2 struct 成員順序不同

### 3. esp_emote_gfx CMakeLists.txt - 格式警告抑制
- 加入 `target_compile_options(${COMPONENT_LIB} PRIVATE -Wno-error=format -Wno-error=format=)`
- 避免 GCC 14 的 designated-init 警告變錯誤

## 使用方式

1. 將檔案覆蓋到 XiaoZhiCode_V2.1.0 專案根目錄
2. 執行 `idf.py build` 編譯
3. 執行 `idf.py -p /dev/ttyACM0 flash` 燒錄

## 備份資訊
- 建立時間：2026-07-01
- ESP-IDF 版本：v5.4.2
- 板子：Waveshare ESP32-S3-Touch-LCD-4B
- 介面：RGB 16-bit 並口 ST7701
