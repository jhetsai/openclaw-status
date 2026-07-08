# 自訂快速指令（已註冊於 MEMORY.md）
| 指令        | 功能說明                                |
|-------------|----------------------------------------|
| /sys        | 顯示完整系統狀態（多行格式）：OpenClaw版本 · Gateway運行時間 · Model · CPU · 記憶體 · 磁碟 · OpenRouter額度 · Brave額度 |
| /or         | 快速查詢 OpenRouter 額度與使用量       |
| /mo list    | 列出所有已註冊的模型簡稱與說明        |
| /mo <簡稱> | 以簡稱切換模型（例如 /mo free）        |

## 投資資產記錄（2026-06-18 更新）

### USD 美金現金結餘
- 資料來源：`assets/portfolio_data.json`（`cash_usd: 14575.98`）
- 2026-06-18：$14,575.98 USD
- 2026-05-08：$14,554.63 USD（+US$21.35，差額來源待查）
- portfolio_data.json 已同步
- 2026-06-18 更新：$14,575.98 + $35.03 = $14,611.01

## ⚠️ 兩個 ESP32 專案架構（2026-07-08 更新）

> 注意！這是兩個不同的硬體、不同 Framework，程式碼完全分開。

### 專案一：ESP32-S3-Touch-LCD-4.3B（Portfolio App）
| 項目 | 內容 |
|------|------|
| **硬體** | ESP32-S3-Touch-LCD-4B (Waveshare) 4.3" IPS Touch (480x480) |
| **Framework** | ESP-IDF |
| **Board** | WAVESHARE_S3_TOUCH_LCD_4B |
| **燒錄位置** | `/dev/ttyACM0` |
| **專案路徑** | `esp32-rlcd-project/02_Example/ESP32-S3-Touch-LCD-4.3B/` |
| **WiFi** | SSID: IoT / 密碼: 057851463 |

**顯示佈局（480×480 面板）：**
```
y=0, h=45   Header（蝦助攻客 | WiFi | 12:34）
y=50, h=80  天氣卡片（滿版寬度）
y=135        持股 + 現金 + 匯率（2×2 網格）
  左(8,135)     持股卡片（232×290）← 左側滿高度
  右上(248,135) 現金卡片（224×140）← 右側上半，4行
  右下(248,283) 匯率卡片（224×142）← 右側下半
```

**重要修改（每次重燒需確認）：**
1. sdkconfig：`CONFIG_BOARD_TYPE_WAVESHARE_S3_TOUCH_LCD_4B=y`
2. esp32-s3-touch-lcd-4b.cc：GT911 touch init struct修正
3. esp_emote_gfx CMakeLists.txt：加 `-Wno-error=format`

**2026-07-07 待解決問題：**
| 問題 | 狀態 |
|------|------|
| WiFi Connected callback (`SetNetworkEventCallback`) 未被呼叫 | ❌ 需燒新韌體驗證 |
| 首頁 WiFi 狀態大字未顯示 `✅ WiFi OK` | ❌ 需燒新韌體後觀察 |
| 天氣顯示 `--°C` 未更新 | ❌ 需燒新韌體後觀察 |
| 持股顯示 `$0` 未更新 | ❌ 需燒新韌體後觀察 |
| 燒錄中斷（新韌體未完整燒入） | ❌ 需重新燒錄 |

---

### 專案二：ESP32-S3-RLCD-4.2（Arduino 天氣時鐘）
| 項目 | 內容 |
|------|------|
| **硬體** | ESP32-S3 + ST7305 4.2" LCD (400x300) + PCF8563 RTC |
| **Framework** | Arduino IDE |
| **程式路徑** | `esp32-rlcd-project/02_Example/Arduino/ESP32-S3-RLCD-4.2/ESP32-S3-RLCD-4.2.ino` |
| **WiFi** | SSID: IoT / 密碼: 057851463 |
| **燒錄方式** | 完整抹除 + 分區燒錄（esptool） |

**架構：**
- Ubuntu Cron 每10分鐘抓天氣 → 上傳 R2 (`tmp/weather.json`)
- ESP32 定時下載 R2 JSON → 解析 → 顯示 + Telegram Debug
- 天氣 API URL: `https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/tmp/weather.json`
- Portfolio API URL: `https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/assets/esp32_portfolio.json`
- Telegram Bot Token: `879343...ER8A`

**顯示配置（400×300，無分隔線）：**
- y=22：日期+星期（9x15）
- y=138：時鐘 62pt（logisoso62_tn）
- y=200：溫度+濕度+電壓（9x15B Bold）
- y=270：WiFi 狀態（6x13）
- Portfolio 右上角：更新時間（right-aligned, y=20）

**WiFi 自動重連（2026-07-02）：**
- `checkWiFi()` 在 `loop()` 裡每 60 秒檢查一次 `WiFi.status()`
- 斷線時：`WiFi.disconnect()` → `WiFi.begin()` 重連，最長等 10 秒

**關鍵修正：**
- `lcd.begin(0, U8G2_R1)` full-buffer 需要 ~273KB，記憶體不足 → 改 `lcd.begin(1, U8G2_R0)` partial-buffer（~91KB）
- ESP32-S3 內建溫度感測器不相容（導致當機），只能顯示天氣 API 溫度
- JSON `"updated": "..."`（冒號後有空格）解析曾導致日期顯示錯誤

**待解決問題：**
| 問題 | 狀態 |
|------|------|
| **編譯失敗** - esp_emote_gfx 與 IDF v5.4.2 不相容 | ❌ 未解決 |
| WiFi LCD 狀態圖示 | ⚠️ 待驗證 |

---

### WiFi 最小測試 Sketch（2026-07-08）
- 路徑：`esp32-rlcd-project/02_Example/Arduino/99_WiFi_Test/99_WiFi_Test.ino`
- 用途：測試 ESP32-S3 能否成功連線 IoT WiFi
- Board：`ESP32S3 Dev Module`
- 燒錄速度：921600 baud

### WiFi 路由器設定
- SSID: `IoT`
- 密碼: `057851463`
- 確認時間：2026-07-07（密碼正確）

## 太陽能發電（2026-06 下半月）
- 梅雨鋒面影響：6/26 大雨（0.1 kWh）、6/27 雷陣雨（0.1 kWh）、6/28 陣雨（0.7 kWh）
- 6月份發電量：11.3 kWh
- 累計進度：6/29 286.5 kWh（梅雨後恢復）
- 頁面：https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/solar/index.html

## MiniMax API 直連 Key（2026-06-23）
- Key: `sk-cp-Iu-vcj6DfStJhSd1WjMae-n3sZxBRA9gEXlKbWN3dvIIVZuFijLzz8iEiTAv0fPvZdrxdJNN9bhVq5ENXJ4Hu18EnkqMpmVW4E6ztNruk9IXa_WxNS6aGH4`
- 存放：OpenClaw SQLite `openclaw-agent.sqlite` 的 `auth_profile_store` 表
- 腳本：`analyze_market_trend.py` 的 `call_minimax_commentary` 已寫死此 key

## 美股配息資料管理規則（2026-07-01 新增）

**問題根因：** `fetch_us_dividend.py` 每次執行會用**當前股數**套用到**所有歷史記錄**，導致歷史配息的股數和金額被錯誤覆寫。

**正確做法：**
- **歷史已入帳記錄**：股數 = 該次配息時的實際持有股數（會隨時間遞增）
  - 例：BND 02/02 除息時持有 113 股 → 歷史記錄必須是 113 股，不能用現在的 118 股
- **Pending 記錄**：用**當前最新股數**（因為還沒入帳，入帳時就是这个股數）
- **div_info**：取所有記錄（confirmed+pending）中 payout/ex_date 最新的那一筆 per_share

**正確 BND 歷史資料（2026）：**
| 支付日 | 每股股利 | 股數 | 實領(USD) |
|--------|---------|------|----------|
| 06/01 | $0.247259 | 117 | $20.25 |
| 05/01 | $0.242 | 116 | $19.65 |
| 04/01 | $0.25 | 115 | $20.12 |
| 03/02 | $0.228 | 114 | $18.19 |
| 02/02 | $0.245 | 113 | $19.38 |

**Pending BND（07/01 除息，07/06入帳）：** 股數 = **118**（當前持有）

**fetch_us_dividend.py 已知問題：**
- `past_cutoff = today - 60天` 會錯誤排除月配 ETF（如 BND）以外的早期記錄
- AAPL 02/09、MSFT 02/19 等 2026Q1 記錄會被 60 天界線過濾掉
- 解決：**不能完整重建**，只能 add-only 模式

**fetch_us_dividend.py 未來執行原則：**
- **禁止完整重建** US confirmed 記錄（會用當前股數覆蓋歷史、60天限制會漏掉記錄）
- 只能 add-only（只比對 key 是否存在，存在則跳過）
- BND 歷史用手動維護（推薦）

**TW 股息規則：**
- 同一人（CHEWEI TSAI）持有期間股數通常不變，風險較低
- 但「2025/12 除息→2026/01 入帳」的 4 筆應歸類為 2025Q4 或 2026Q1 需確認（目前有 00940、00712、00713、009802 跨年記錄）

## Promoted From Short-Term Memory (2026-07-04)

<!-- openclaw-memory-promotion:memory:memory/2026-06-29.md:37:39 -->
- ESP32 程式: 檔案: `esp32-rlcd-project/02_Example/Arduino/ESP32-S3-RLCD-4.2/ESP32-S3-RLCD-4.2.ino`; 功能: WiFi + NTP + RTC + R2 天氣 + 螢幕 + Telegram Debug; 螢幕初始化: `lcd.begin(1, U8G2_R0)`（已修正） [score=0.823 recalls=0 avg=0.620 source=memory/2026-06-29.md:37-39]

## Promoted From Short-Term Memory (2026-07-05)

<!-- openclaw-memory-promotion:memory:memory/2026-07-01.md:15:15 -->
- 待解決問題: **問題1：WiFi 從未成功連線** [score=0.820 recalls=0 avg=0.620 source=memory/2026-07-01.md:15-15]
<!-- openclaw-memory-promotion:memory:memory/2026-07-01.md:16:19 -->
- 待解決問題: ESP32 WiFi init 順序：`esp_wifi_init` → `esp_wifi_set_mode(STA)` → `esp_wifi_set_config` → `esp_wifi_start` → `esp_wifi_connect`; `getaddrinfo() returns 202` = DNS 解析失敗，但根本原因是 **WiFi 還沒連上 AP**（路由器可能拒絕連線或密碼錯誤）; IoT 路由器密碼可能不是 `057851463`，需要使用者確認; UART 看不見 `esp_rom_printf` 早期輸出（USB CDC 初始化時機問題） [score=0.820 recalls=0 avg=0.620 source=memory/2026-07-01.md:16-19]
<!-- openclaw-memory-promotion:memory:memory/2026-07-01.md:21:21 -->
- 待解決問題: **問題2：LCD WiFi 狀態圖示看不見** [score=0.820 recalls=0 avg=0.620 source=memory/2026-07-01.md:21-21]
<!-- openclaw-memory-promotion:memory:memory/2026-07-01.md:22:23 -->
- 待解決問題: 程式碼已寫入，但韌體燒的是還沒完整編譯成功的版本（build failed）; 需要等問題3修復後才能燒新版韌體 [score=0.820 recalls=0 avg=0.620 source=memory/2026-07-01.md:22-23]
<!-- openclaw-memory-promotion:memory:memory/2026-07-01.md:25:25 -->
- 待解決問題: **問題3：編譯失敗 - esp_emote_gfx 與 IDF v5.4.2 不相容** [score=0.820 recalls=0 avg=0.620 source=memory/2026-07-01.md:25-25]
<!-- openclaw-memory-promotion:memory:memory/2026-07-01.md:26:28 -->
- 待解決問題: 錯誤：`esp_log_color.h: error: format '%d' expects argument of type 'int', but argument has type 'uint32_t'`; 位置：`managed_components/espressif2022__esp_emote_gfx/src/core/gfx_refr.c:117`; 原因：第三方元件使用 `%d` 格式化 `uint32_t`，IDF v5.4.2 把 `-Wformat` 警告當成錯誤 [score=0.820 recalls=0 avg=0.620 source=memory/2026-07-01.md:26-28]
<!-- openclaw-memory-promotion:memory:memory/2026-06-30.md:33:36 -->
- 每日排程: | 每天 15:00 | `gen_portfolio_data.py` 持股總攬 | ✅ 19:01 正常 | | 每天 20:00 | `update_dividend_data.py` 除息資料更新 | ✅ R2 上傳成功 | | 每天 08:00, 12:00, 18:00 | `wind-alert.sh` 風速警示 | ✅ 19.0 km/h 已發送 | | 每天 09:00 | `cron_us_dividend.py` 美股除息行事曆 | ✅ 無待入帳 | [score=0.812 recalls=0 avg=0.620 source=memory/2026-06-30.md:33-36]

## Promoted From Short-Term Memory (2026-07-06)

<!-- openclaw-memory-promotion:memory:memory/2026-07-02.md:13:16 -->
- ESP32-S3-RLCD-4.2 Portfolio 頁面日期顯示修復: 需求：右上角顯示 esp32_portfolio.json 的 updated 時間; 問題：JSON 是 `"updated": "2026-07-02 13:51"`（冒號後有空格），但程式搜尋 `"updated":"`（無空格），導致解析失敗，右上角永遠顯示 `...`; 修復：搜尋改為 `"updated":"`（10 chars），`up += 10` 然後 skip space 和 opening quote; 程式：/home/jhe/.openclaw/workspace/esp32-rlcd-project/02_Example/Arduino/ESP32-S3-RLCD-4.2/ESP32-S3-RLCD-4.2.ino [score=0.815 recalls=0 avg=0.620 source=memory/2026-07-02.md:13-16]
<!-- openclaw-memory-promotion:memory:memory/2026-07-02.md:4:6 -->
- 發電記錄（累積）: 2026-07-01：天氣：早晨27°C/84%濕度/薄霧，午後短暫雨，30°C/68%/11km/h，傍晚至夜間：30°C/68%/11km/h，Partly Cloudy; 2026-07-02：天氣：早晨27°C/84%/薄霧，☀️ 白天高溫33°C/UV 9; 累積總發電量：288.8 kWh（2026-07-02）; 日發電：0.7 kWh; 天氣：局部小雨，氣溫28°C，體感30°C，濕度82%，風速4km/h，UV 0 [score=0.815 recalls=0 avg=0.620 source=memory/2026-07-02.md:4-6]
<!-- openclaw-memory-promotion:memory:memory/2026-07-02.md:9:10 -->
- 美元現金結餘更新: 2026-07-02：$14,628.00 USD（從 portfolio_data.json 更新）; 資料來源：頁面截圖確認 [score=0.815 recalls=0 avg=0.620 source=memory/2026-07-02.md:9-10]

## Ubuntu 系統排程（/etc/cron.d/jhe-crons）

> 2026-07-06 整理：所有排程集中在此，日後詢問「系統排程」即查閱此處。

| 時間 | 任務 | 輸出日誌 |
|---|---|---|
| `*/10 21-23,0-4 * * 0-6` | cron-stock-update.sh（美股時段） | — |
| `*/10 9-13 * * 0-6` | cron-stock-update.sh（台股時段） | — |
| `*/30 6-8,14-21 * * 0-6` | cron-stock-update.sh（非交易時段） | — |
| `0 * * * *` | cron-status-update.sh | — |
| `*/30 * * * *` | fetch-weather-to-r2.sh | logs/weather.log |
| `0 8,12,18 * * *` | wind-alert.sh | logs/wind_alert.log |
| `0 */6 * * *` | fetch_tw_dividend_detail.py | logs/cron-stock.log |
| `0 20 * * *` | update_dividend_data.py | logs/dividend_update.log |
| `0 15 * * *` | gen_portfolio_data.py | logs/cron-stock.log |
| `*/30 9-16 * * 1-5` | scrape_taiwan_bank_rate.py | logs/exchange_rate.log |
| `0 9 * * *` | cron_us_dividend.py | logs/us_dividend_cron.log |
| `*/30 9-13 * * 0-6` | fetch_volume_rank.py | logs/volume_cron.log |
| `0 14 * * 0-6` | fetch_volume_rank.py（收盤後一次） | logs/volume_cron.log |
| `@reboot` | vm_boot_notify.sh | — |
| `5 14 * * 0-6` | analyze_market_trend.py（每日市場分析） | logs/volume_cron.log |
| `0 16 */3 * *` | etl_memory_with_notify.sh | scripts/pgvector/logs/etl_memory.log |
| `0 9 * * 0` | us_tech_report.py | logs/us_tech_report.log |
| `0 10 * * 3,6` | crypto_report.py | logs/crypto_report.log |
| `0 10 * * 5` | us_giants_report.py | logs/us_giants_report.log |
| `0 10 * * 1,4` | pokemon_30th_report.py | logs/pokemon_report.log |

**注意：** OpenClaw Cron（`cron` tool）僅用於 OpenClaw 自身任務（如 Memory Dreaming），系統排程統一由 Ubuntu `/etc/cron.d/jhe-crons` 管理，兩者不可混用。

## Promoted From Short-Term Memory (2026-07-07)

<!-- openclaw-memory-promotion:memory:memory/2026-07-02.md:17:18 -->
- ESP32-S3-RLCD-4.2 Portfolio 頁面日期顯示修復: 燒錄：/dev/ttyACM0（esptool 燒錄成功）; 狀態：✅ 已完成（2026-07-02 15:20） [score=0.845 recalls=0 avg=0.620 source=memory/2026-07-02.md:17-18]
<!-- openclaw-memory-promotion:memory:memory/2026-07-02.md:21:24 -->
- ESP32-S3-RLCD-4.2 WiFi 自動重連（2026-07-02 新增）: 每 60 秒檢查一次 `WiFi.status()`; 斷線時：`WiFi.disconnect()` → `WiFi.begin()` 重連，最長等 10 秒; 連上後自動恢復 fetch，連不上顯示 `WiFi OFF`; 程式：`checkWiFi()` 函數在 `loop()` 裡每分鐘執行一次 [score=0.845 recalls=0 avg=0.620 source=memory/2026-07-02.md:21-24]
<!-- openclaw-memory-promotion:memory:memory/2026-07-02.md:25:25 -->
- ESP32-S3-RLCD-4.2 WiFi 自動重連（2026-07-02 新增）: 狀態：✅ 已完成（2026-07-02 15:20） [score=0.845 recalls=0 avg=0.620 source=memory/2026-07-02.md:25-25]

## ⚠️ ESP32-S3-Touch-LCD-4.3B 專案路徑確認（2026-07-08 新增）

**正確資料夾（重要）：**
- 「02_Example/ESP32-S3-Touch-LCD-4.3B/」 ← 這個才是 ESP32-S3-Touch-LCD-4.3B Portfolio App 所在
- `main/application_portfolio.cc` 和 `application_portfolio.h` 是主要修改的檔案
- `PortfolioDashboard/` 是另一個舊專案，**不是**目標

**今日 Commits（2026-07-08，都在 XiaoZhiCode_V2.1.0/）：**
- `b878051b`: 2x2 grid layout, cash parsing bugfix
- `b55de34b`: Chinese font (font_puhui), thousands separator
- `b3a49af1`: Fix Run() must not return - while(1) keep-alive loop
- `d0d967b7`: Portfolio App major rewrite, crt_bundle HTTPS, 480x480 layout
- `982918a5`: Move SetNetworkEventCallback before StartNetwork

**Flash Issue（已解決 2026-07-08）：**
- **根本原因**：partition table `ota_0` 只有 4MB，但 binary 大小 4.34MB（溢出 239KB）
- esptool 不檢查 partition 大小，資料寫到 partition 外 → app 損壞 → 無顯示
- **解決**：修改 `partitions/v2/16m.csv`，`ota_0`/`ota_1` 從 4MB → 5MB
- **正確燒錄流程**：`idf.py erase-flash` → `idf.py flash`
- 燒錄位置：`/home/jhe/.openclaw/workspace/esp32-rlcd-project/02_Example/XiaoZhi/XiaoZhiCode_V2.1.0/`
