# ESP32-S3-Touch-LCD-4B 研究報告

> 日期：2026-06-30 初版研究
> 更新：2026-07-01 完成燒錄
> 板子：Waveshare ESP32-S3-Touch-LCD-4B

---

## 硬體總覽

| 項目 | 規格 |
|------|------|
| 螢幕 | 4" RGB 480×480, ST7701, 65K彩色, 電容觸控 |
| 處理器 | ESP32-S3R8, 240MHz, 雙核 |
| 記憶體 | 16MB Flash + 8MB PSRAM |
| 音訊 | ES8311 (播放) + ES7210 (收音+AEC) |
| IMU | QMI8658 (三軸加速度+陀螺儀) |
| RTC | PCF85063 |
| 電源 | AXP2101 (燃料計, 真正的電量%) |
| 電池 | 3.7V鋰電池 (PH2.0接口) |
| 開發方式 | Arduino / ESP-IDF |

---

---

## ✅ 成功燒錄（2026-07-01）

### 正確來源
**`XiaoZhiCode_V2.1.0`**（ESP-IDF）
- 路徑：`/home/jhe/.openclaw/workspace/esp32-rlcd-project/02_Example/XiaoZhi/XiaoZhiCode_V2.1.0`
- 正確介面：**RGB 16-bit 並口**（`esp_lcd_rgb_panel` + `st7701`）
- Board type：`WAVESHARE_S3_TOUCH_LCD_4B`

### 燒錄指令
```bash
# 燒錄（確認序列埠 /dev/ttyACM0）
cd /home/jhe/.openclaw/workspace/esp32-rlcd-project/02_Example/XiaoZhi/XiaoZhiCode_V2.1.0
source ~/esp/esp-idf-v5.4.2/export.sh
idf.py -p /dev/ttyACM0 flash

# 或用 esptool 直接燒（燒完重燒時用）
python3 -m esptool --chip esp32s3 -p /dev/ttyACM0 -b 460800 \
  --before=default_reset --after=hard_reset write-flash \
  --flash-mode dio --flash-freq 80m --flash-size 16MB \
  0x0 build/bootloader/bootloader.bin \
  0x8000 build/partition_table/partition-table.bin \
  0xd000 build/ota_data_initial.bin \
  0x20000 build/xiaozhi.bin
```

### 燒錄位置
- USB序列埠：`/dev/ttyACM0`（燒錄用）
- `/dev/ttyACM1`（系統監控）

### 必須修改的檔案（編譯前）

1. **sdkconfig**（燒錯board type）
   - 路徑：`XiaoZhiCode_V2.1.0/sdkconfig`
   - 將 `CONFIG_BOARD_TYPE_BREAD_COMPACT_WIFI=y` 改為 `# CONFIG...is not set`
   - 將 `# CONFIG_BOARD_TYPE_WAVESHARE_S3_TOUCH_LCD_4B is not set` 改為 `CONFIG_BOARD_TYPE_WAVESHARE_S3_TOUCH_LCD_4B=y`

2. **esp_lcd_touch_gt911**巨集不相容（燒綠錯誤）
   - 檔案：`main/boards/waveshare-s3-touch-lcd-4b/esp32-s3-touch-lcd-4b.cc`
   - 位置：約第280行
   - 將巨集 `ESP_LCD_TOUCH_IO_I2C_GT911_CONFIG()` 改為手動初始化struct（因為ESP-IDF v5.4.2 struct成員順序不同）

3. **esp_emote_gfx 格式字串警告**（在ESP-IDF v5.4.2會變錯誤）
   - 檔案：`managed_components/espressif2022__esp_emote_gfx/CMakeLists.txt`
   - 尾端加入：
     ```cmake
     target_compile_options(${COMPONENT_LIB} PRIVATE -Wno-error=format -Wno-error=format=)
     ```

### 激活方式
1. 連上熱點 `Xiaozhi-E709`，瀏覽器打開 `192.168.4.1` 設定WiFi
2. 設備會顯示6位驗證碼（如 `042382`）
3. 去 https://xiaozhi.me/ 註冊/登入
4. 在 Console 新增設備，輸入驗證碼完成激活

### ❌ 不能用的專案
- `09_LVGL_V9_Test`（SPI介面，RLCD專案）
- `10_FactoryProgram`（同SPI RLCD）

---

## 現有可用範例

| 範例 | 功能 | 對專案價值 |
|------|------|-----------|
| 01_HelloWorld | GFX 基本繪圖 | 參考螢幕初始化 |
| 02_GFX_AsciiTable | RGB LCD GFX 操作 | 圖形繪製參考 |
| 03_LVGL_PCF85063 | LVGL + RTC 時間顯示 | LVGL 架構學習 |
| 04_LVGL_QMI8658_ui | LVGL + IMU 繪圖 | LVGL 圖表實作 |
| 05_LVGL_AXP2101_ADC | LVGL + AXP2101 電量顯示 | 電源管理實作 |
| 06_LVGL_Arduino_v9 | LVGL Widget 演示 | LVGL 觸控 UI 完整範例 |
| 07_ES8311 | I2S 音頻播放 | 語音輸出基礎 |
| 08_ES7210 | I2S 收音 (AEC) | 語音輸入基礎 |

---

## 專案一：互動式投資儀表板

### 架構

```
韌體 (Arduino/ESP-IDF)
  ├── LVGL v9          → 觸控 UI (480×480 彩色)
  ├── WiFi Client      → HTTPS 抓取 R2 JSON
  ├── AXP2101          → 顯示真正的電量%
  └── PCF85063         → RTC 時鐘

資料來源（與 RLCD 版共用）：
  https://pub-xxx.r2.dev/assets/esp32_portfolio.json
```

### 功能規劃

1. **首頁（總覽）**
   - 總資產市值 + 報酬率（大字）
   - 台股/美股兩欄卡片
   - 觸控按鈕進入個股

2. **持股詳情頁**
   - 點擊任一股票 → 該檔詳情
   - 成本均價 / 現在股價 / 帳面增益
   - 柱狀圖顯示相對於成本的 %

3. **匯率面板**
   - USD/TWD, JPY/TWD 即時
   - 來自 `esp32_portfolio.json` 的 fx 欄位

4. **電量（真正燃料計）**
   - AXP2101 直接讀取，數字精準
   - 不再用電壓估算

### LVGL 關鍵技巧

```cpp
// 觸控輸入設備（已有 GT911 驅動）
lv_indev_t * indev = lv_indev_create();
lv_indev_set_type(indev, LV_INDEV_TYPE_POINTER);
lv_indev_set_read_cb(indev, gt911_read_cb);

// 圖表（借鑒 04_LVGL_QMI8658_ui）
lv_obj_t * chart = lv_chart_create(parent);
lv_chart_set_type(chart, LV_CHART_TYPE_BAR);

// 頁面切換
lv_scr_load_anim(screen_new, LV_SCR_LOAD_ANIM_MOVE_LEFT, 300, 0, true);
```

### 與 RLCD 版的差異

| 項目 | RLCD-4.2 | Touch-LCD-4B |
|------|----------|--------------|
| 更新方式 | GPIO 按鍵切換 | 觸控滑動 |
| 顏色 | 灰階 | 65K 彩色 |
| 顯示 | 純數字 | 圖表+卡片+顏色 |
| 電量 | 電壓估算 | AXP2101 燃料計 |
| 音訊 | 無 | 喇叭+麥克風 |

### 開發順序建議

1. 先燒 06_LVGL_Arduino_v9 確認 LVGL 觸控正常
2. 整合 05_LVGL_AXP2101_ADC_Data 確認電量讀數
3. 修改為自己的投資組合頁面
4. 加入 WiFi + HTTP fetch JSON

---

## 專案二：智能語音助理

### 硬體語音鏈

```
[ES7210 麥克風] → I2S → [ESP32-S3 處理] → I2S → [ES8311 喇叭]
                                        ↓
                                   WiFi → [OpenAI TTS/STT]
                                        ↓
                                   WiFi → [LLM API]
```

### 語音處理流程

```
1. 喚醒偵測（Wake Word）
   - 在 ES7210 麥克風上用簡單 energy detection
   - 類語音訊號 → threshold trigger
   - 替代方案：按下按鍵喚醒（最穩定）

2. 收音（ES7210, I2S, 16kHz）
   - ADC 收音，通過 I2S 傳輸
   - AEC (回聲消除) 晶片幫助過濾環境噪音
   - 緩衝區：I2S DMA 雙緩衝

3. 語音辨識（STT）
   - 將 PCM 封裝成 WAV/OGG
   - 送至 OpenAI Whisper API（文字化）
   - 或本地離線辨識（需模型）

4. 對話生成（LLM）
   - OpenAI GPT-4o-mini API（便宜的 reasoning）
   - prompt 設計：角色+理財助理人格

5. 語音輸出（TTS）
   - ElevenLabs / OpenAI TTS API
   - 回傳音檔 → I2S → ES8311 播放
```

### 關鍵代碼參考

**ES8311 播放（範例 07）：**
```cpp
// I2S 設定
I2S.begin(I2S_LRCK_PIN, I2S_DATA_PIN, sampleRate, I2S_DATA_BIT_WIDTH, channelFormat);
// 播放 PCM 資料
i2s.write(pcm_buffer, buffer_size);
```

**ES7210 收音（範例 08）：**
```cpp
// I2S DMA 雙緩衝收音
i2s_reader_t reader;
reader.init(i2s_port, I2S_SCK_PIN, I2S_WS_PIN, I2S_SD_PIN, 16000);
reader.start([](const void* data, size_t len) {
    // 音訊資料處理
});
```

**喚醒偵測（簡化版）：**
```cpp
// 偵測麥克風 energy
int16_t sample = get_mic_sample();
uint32_t energy = rolling_energy(sample);
if (energy > ENERGY_THRESHOLD && !isPlaying) {
    startRecording();
}
```

### 實用功能建議

| 功能 | 說明 |
|------|------|
| 持股語音播報 | 「今天帳面賺了多少？」→ 語音回答 |
| 智働天氣 | 「明天雲林天氣如何？」 |
| 定时播報 | 每天早上 8:00 主動語音播報 |
| 按鍵喚醒 | 按一下 PWR 鍵，開始收音 |

### 與 RLCD 版的整合

- 語音回答結果可以顯示在 RLCD 螢幕上
- 兩塊板子透過 BLE 或 UART 溝通
- Touch-LCD-4B 負責語音 I/O，RLCD 負責顯示

---

## 開發環境準備

### 需要安裝的 Library（Arduino）

| 庫 | 版本 | 安裝方式 |
|----|------|---------|
| GFX_Library_for_Arduino | v1.6.0 | 線上/離線 |
| lvgl | v9.3.0 | 離線（含demos）|
| SensorLib (QMI8658/GT911/PCF85063) | v0.3.1 | 線上/離線 |
| XPowersLib (AXP2101) | v0.2.6 | 線上/離線 |
| MyLibrary (板子巨集) | - | 離線 |
| lv_conf.h | - | 離線 |

### 板子設定（Arduino IDE）

1. Board: `ESP32S3 Dev Module`
2. Port: USB CDC → Enable
3. Partition: `No OTA (2MB APP)`
4. Flash Size: `16MB`
5. PSRAM: `8MB`

---

## 待確認事項

- [ ] 是否已安裝 Arduino ESP32 core v3.2.0+？
- [ ] 板子的 I2C/SPI GPIO 腳位對照（需確認接線）
- [ ] WiFi 連接方式（直接燒錄或配網flow）？
- [ ] TTS 用 ElevenLabs 還是 OpenAI TTS（需金鑰）？
- [ ] 要支援喚醒詞偵測還是純按鍵喚醒？
