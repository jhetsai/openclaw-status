# ESP32-S3-Touch-LCD-4B × OpenClaw 整合規劃（確認版）

> 日期：2026-06-30
> 確認：① R2 JSON上傳  ② WiFi 燒死  ③ 語音助理整合

---

## 📦 最終系統架構

```
┌─────────────────────────────────────────────────────────┐
│                         VM                              │
│  ┌─────────────────┐    ┌─────────────────────────────┐ │
│  │ openclaw-status │───▶│  gen_status_json.py         │ │
│  │ HTML page       │    │  (merge system+solar+api    │ │
│  └─────────────────┘    │   +portfolio into one JSON)  │ │
│                         └──────────┬──────────────────┘ │
│                                    │  每30秒寫入          │
│                                    ▼                     │
│                         /workspace/assets/              │
│                            status_esp32.json            │
│                                    │                    │
│                         ┌──────────┴──────────────────┐ │
│                         │  scripts/upload_status.sh   │ │
│                         │  (R2: status_esp32.json)    │ │
│                         └──────────┬──────────────────┘ │
│                                    │  每30秒上傳         │
└────────────────────────────────────┼────────────────────┘
                                     ▼
              ┌──────────────────────────────────────────┐
              │           Cloudflare R2 CDN             │
              │  status_esp32.json (public read)        │
              └──────────────┬──────────────────────────┘
                             │ WiFi GET (HTTPS)
                             ▼
         ┌───────────────────────────────────────────┐
         │       ESP32-S3-Touch-LCD-4B               │
         │  ┌─────────────────────────────────────┐ │
         │  │ LVGL UI (5頁 觸控滑動)              │ │
         │  │  ① 系統總覽  ② 太陽能               │ │
         │  │  ③ 投資組合  ④ API額度              │ │
         │  │  ⑤ 服務狀態                          │ │
         │  ├─────────────────────────────────────┤ │
         │  │ AXP2101 燃料計 (電量%)               │ │
         │  │ ES7210 收音 (喚醒/指令)              │ │
         │  │ ES8311 播放 (語音回覆)               │ │
         │  └─────────────────────────────────────┘ │
         └───────────────────────────────────────────┘
```

---

## 📋 5個 LVGL 頁面

| # | 頁面 | 主要資訊 | 更新頻率 |
|---|------|---------|---------|
| 1 | 🖥️ 系統總覽 | 主機名/已開機/RAM/CPU/磁碟 | 30 秒 |
| 2 | ☀️ 太陽能 | 即時發電(W)/今日kWh/天氣/效率 | 1 分鐘 |
| 3 | 💹 投資組合 | 總資產/台股/美股/現金 | 10 分鐘 |
| 4 | 📡 API 額度 | Brave + OpenRouter 進度條 | 10 分鐘 |
| 5 | 🔔 服務狀態 | Telegram/LINE/Cron 狀態 | 1 分鐘 |

---

## 🔄 JSON 上傳流程（R2）

### R2 上的 JSON 格式

```
https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/assets/status_esp32.json
```

```json
{
  "updated": "2026-06-30T13:00:00+08:00",
  "system": {
    "hostname": "jhe-VMware-Virtual-Platform",
    "uptime_str": "0d 5h 32m",
    "mem_used_gb": 2.4,
    "mem_total_gb": 7.7,
    "mem_pct": 31,
    "cpu_pct": 5.0,
    "disk_used_gb": 39,
    "disk_total_gb": 118,
    "node_version": "v22.23.1",
    "model": "MiniMax M2.7"
  },
  "solar": {
    "today_kwh": 1.2,
    "current_watt": 150,
    "efficiency_pct": 100,
    "weather": "晴",
    "temp_c": 33.4,
    "wind_kmh": 3.6
  },
  "portfolio": {
    "total_cost": 2907218,
    "total_mktval": 6239175,
    "total_gain_pct": 114.61,
    "tw_cost": 1820145,
    "tw_mktval": 4370083,
    "tw_gain_pct": 140.1,
    "us_cost_twd": 1224493,
    "us_mktval_twd": 1869092,
    "us_gain_pct": 52.64,
    "usd_cash": 14537.8,
    "usd_rate": 31.922,
    "jpy_cash": 611791,
    "jpy_rate": 0.1943
  },
  "api_usage": {
    "brave_used": 0.51,
    "brave_limit": 5.0,
    "openrouter_used": 2.23,
    "openrouter_limit": 5.0
  },
  "services": {
    "telegram": "running",
    "line": "running",
    "cron_wind_alert": "running"
  }
}
```

### 上傳排程（每 30 秒）

```bash
# 現有 cron-stock-update.sh 每 10 分鐘
# + 新增 status-update.sh 每 30 秒
*/1 * * * * /home/jhe/.openclaw/workspace/scripts/gen_status_json.py && \
  /home/jhe/.openclaw/workspace/scripts/upload_status_r2.sh
```

---

## 🎤 語音助理整合

### 語音流程

```
按 PWR 鍵
    │
    ▼
[ES7210 收音] ── I2S DMA ──▶ ESP32-S3 緩衝
                                     │
                              錄滿 30 秒 WAV
                                     │
                              切換 WiFi HTTPS
                                     │
                                     ▼
                          [OpenAI Whisper API]
                                     │  (text)
                                     ▼
                          [MiniMax LLM API]
                                     │  (reply text)
                                     ▼
                          [ElevenLabs TTS API]
                                     │  (MP3/OGG)
                                     ▼
[ES8311 播放] ◀── I2S DMA ◀── ESP32-S3
```

### 語音功能

| 問法 | 回覆 |
|------|------|
| 「現在系統怎麼樣？」 | 記憶體/CPU/發電量語音報告 |
| 「今天發電多少？」 | 今日 kWh + 天氣 |
| 「總資產多少？」 | 總市值 + 報酬率語音播報 |
| 「API 額度還剩多少？」 | Brave + OpenRouter 剩餘量 |
| 「明天天氣？」 | 四湖測站天氣預報 |

### LVGL 語音 UI

- 按 PWR 鍵時，螢幕邊緣亮綠色框 →「正在收音」
- 語音回覆時，喇叭 icon 閃爍 →「播放中」
- 播放完自動回到原本頁面

---

## 📁 韌體檔案結構

```
esp32-touch-lcd-project/
├── TouchDashboard/
│   ├── TouchDashboard.ino        ← 主程式（LVGL 5頁 + 語音）
│   ├── pages/
│   │   ├── page_system.h        ← 系統總覽頁
│   │   ├── page_solar.h         ← 太陽能頁
│   │   ├── page_portfolio.h     ← 投資組合頁
│   │   ├── page_api.h           ← API 額度頁
│   │   └── page_services.h      ← 服務狀態頁
│   ├── network/
│   │   └── wifi_client.h        ← WiFi + HTTPS fetch
│   ├── voice/
│   │   └── voice_assistant.h    ← 錄音+Whisper+TTS
│   ├── display/
│   │   └── lvgl_init.h          ← LVGL + 觸控初始化
│   ├── power/
│   │   └── axp2101.h            ← 電量+背光
│   └── assets/
│       └── icons/               ← 圖示資源
└── README.md
```

---

## 🔧 實作順序

### Step 1：VM 端（JSON 生成 + 上傳）

```
① gen_status_json.py    ─ 讀取 system/solar/api/portfolio 寫入 status_esp32.json
② upload_status_r2.sh   ─ 上傳 R2
③ crontab */1 * * * *   ─ 每分鐘執行
```

### Step 2：ESP32 韌體（LVGL 顯示）

```
① 燒錄 06_LVGL_Arduino_v9  ─ 確認 LVGL 觸控正常
② 燒錄 05_LVGL_AXP2101_ADC ─ 確認 AXP2101 電量讀數
③ 燒錄 07_ES8311            ─ 確認音訊播放正常
④ 燒錄 08_ES7210            ─ 確認收音正常
⑤ 整合：WiFi + HTTP fetch JSON + LVGL 5頁
```

### Step 3：語音助理

```
① 錄音框架（I2S DMA 雙緩衝）
② Whisper STT 整合
③ TTS 整合（ElevenLabs）
④ 對話 Prompt 設計
⑤ LVGL 語音 UI（收音/播放 視覺回饋）
```

---

## ⏱️ 預估時程

| 階段 | 工作 | 優先序 |
|------|------|--------|
| **VM** | gen_status_json.py + 上傳 R2 | P0（最先做）|
| **韌體** | LVGL 5頁顯示 | P1 |
| **韌體** | WiFi + JSON fetch | P1 |
| **韌體** | 觸控滑動切頁 | P2 |
| **韌體** | AXP2101 電量 | P2 |
| **語音** | ES7210 錄音 + Whisper | P3 |
| **語音** | ES8311 播放 + TTS | P3 |

---

## 📝 待確認

- [ ] ElevenLabs API Key 有嗎？（語音輸出需要）
- [ ] ESP32-S3-Touch-LCD-4B 有沒有插 WiFi 天線？（訊號穩定性）
- [ ] 家裡 WiFi SSID + Password 是什麼？（燒進去）
- [ ] 想把這塊放哪裡？（固定位置供電 or 移動攜帶）
