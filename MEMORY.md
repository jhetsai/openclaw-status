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

**2026-07-10 時鐘維修完成 ✅：**
| 問題 | 原因 | 修復 |
|------|------|------|
| 秒數落後 3 秒 | esp_timer + lock contention | 改用 `lv_timer_create()` |
| WiFi 連線後時鐘亂跳 | SNTP init 太晚 | Initialize() 直接 init SNTP |
| NTP sync 延遲 | WiFi 慢 | 每 10 秒用 `time()` Fallback |
| RSSI fetch 失敗 | WiFi callback stack 太小 | 移到 LvglTask |

**韌體版本：** `2.1.0`（App version）| Commit: `756daa7a`
**韌體備份：** `/home/jhe/.openclaw/workspace/backups/2026-07-10/`
- `xiaozhi_2026-07-10_1534.bin` — 主韌體（4.3MB）
- `partition-table_2026-07-10.bin` — 分區表
- `bootloader_2026-07-10.bin` — Bootloader
- `application_portfolio.cc/h` — 原始碼
- `memory_2026-07-10.md` — 維修日誌
- `README.md` — 還原說明

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

## Promoted From Short-Term Memory (2026-07-10)

<!-- openclaw-memory-promotion:memory:memory/2026-07-06.md:10:11 -->
- 現況: `PopulateScanResults()` ❌ 完全沒被執行過（log 從未出現）; Watchdog timeout 導致 CPU 0 閒置任務無法執行 [score=0.818 recalls=0 avg=0.620 source=memory/2026-07-06.md:10-11]
<!-- openclaw-memory-promotion:memory:memory/2026-07-06.md:14:14 -->
- 根本原因（懷疑）: **LvglTask 可能從未成功啟動，或啟動後立即崩潰** [score=0.818 recalls=0 avg=0.620 source=memory/2026-07-06.md:14-14]
<!-- openclaw-memory-promotion:memory:memory/2026-07-06.md:17:19 -->
- 根本原因（懷疑）: `ESP_LOGI(TAG, "LVGL task started")` 在整個 UART log 中**從未出現**; LvglTask 負責：touch polling + `wifi_scan_done_pending_` check + `PopulateScanResults()`; LvglTask 如果死了 → `PopulateScanResults()` 不會被呼叫 [score=0.818 recalls=0 avg=0.620 source=memory/2026-07-06.md:17-19]
<!-- openclaw-memory-promotion:memory:memory/2026-07-06.md:22:24 -->
- 懷疑 LvglTask stack overflow: 目前 stack：8192 bytes（太小）; LVGL `lv_task_handler()` + touch indev operations 可能需要更多; 修復：增加到 **12288 bytes** [score=0.818 recalls=0 avg=0.620 source=memory/2026-07-06.md:22-24]
<!-- openclaw-memory-promotion:memory:memory/2026-07-06.md:27:29 -->
- 其他發現: Watchdog timeout：CPU 0 IDLE0 任務長期無法執行，每 6.5 秒触发一次; `WifiScanTask` 是獨立的 task（core 1），不受 LvglTask 影響; 按鈕座標：x=20~460, y=120~200 [score=0.818 recalls=0 avg=0.620 source=memory/2026-07-06.md:27-29]
<!-- openclaw-memory-promotion:memory:memory/2026-07-06.md:32:34 -->
- 待修（本次）: LvglTask stack：8192 → 12288（在 `xTaskCreatePinnedToCore` 呼叫處）; 加 `fflush(stdout)` 在所有关键 log 後，確保 UART 及時輸出; `ESP_LOGI(TAG, "LVGL task started")` 後加 `fflush(stdout)` [score=0.818 recalls=0 avg=0.620 source=memory/2026-07-06.md:32-34]
<!-- openclaw-memory-promotion:memory:memory/2026-07-05.md:7:7 -->
- 事件：執行 etl_memory_v2.py（記憶向量化）: **實際結果：** [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-05.md:7-7]
<!-- openclaw-memory-promotion:memory:memory/2026-07-05.md:8:11 -->
- 事件：執行 etl_memory_v2.py（記憶向量化）: 301 個 .md 檔案; 9,383 chunks（寫入 PostgreSQL）; 總耗時：~35 分鐘; 向量嵌入速度：267 chunks/min（CPU 模式） [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-05.md:8-11]
<!-- openclaw-memory-promotion:memory:memory/2026-07-07.md:21:24 -->
- 今日進度: **09:xx**：誤將 XiaoZhiCode_V2.1.0 燒成 Weather Clock（Arduino/11_Weather_Clock），LCD 顯示混亂; **10:xx**：刷回 XiaoZhiCode_V2.1.0（07-06 16:55 build）; 確認 WiFi SSID 掃描正常（CHT Wi-Fi、IoT）; 確認 IoT 路由器密碼 `057851463` [score=0.806 recalls=0 avg=0.620 source=memory/2026-07-07.md:21-24]
<!-- openclaw-memory-promotion:memory:memory/2026-07-07.md:25:25 -->
- 今日進度: 確認韌體燒入位置正確（`idf.py build` + `esptool write_flash`） [score=0.806 recalls=0 avg=0.620 source=memory/2026-07-07.md:25-25]
