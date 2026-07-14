# JHE Cron Backup Container

VM 關機時，用備援機接手 cron 任務寫入 R2。

## 架構

```
VM 正常：VM cron → R2
VM 關機：備援機 Docker cron → R2（ESP32 不需要改）
```

## 部署方式

### 選項 A：Synology NAS / 備援 Linux 機器

```bash
# 1. 複製到備援機
scp -r docker/jhe-cron user@backup-machine:/home/user/

# 2. 建立 workspace（從 VM 或 R2 同步持股資料）
mkdir -p /home/user/workspace
# 複製 taiwan_stocks.json, us_stocks.json 等持股資料

# 3. 設定 API keys
cp env.list.template env.list
# 編輯 env.list，填入實際的 API keys

# 4. 設定 crontab 參考
# 使用 cron.d/jhe-cron-backup 中的排程

# 5. 啟動
docker compose up -d
```

### 選項 B：直接跑 Python 腳本（不需要 Docker）

```bash
# 在備援機上
export R2_ACCESS_KEY="..."
export R2_SECRET_KEY="..."
export FINNHUB_KEY="..."
export CWA_API_KEY="..."
export WEATHER_API_KEY="..."

# 執行天氣更新
bash scripts/fetch-weather-to-r2.sh

# 執行持股更新
bash scripts/cron-stock-update.sh
```

## 需要的資料檔案（持股相關）

這些檔案需要從 VM 或 R2 同步到備援機的 workspace：

| 檔案 | 用途 |
|------|------|
| `taiwan_stock/taiwan_stocks.json` | 台股持股明細 |
| `us_stock/us_stocks.json` | 美股持股明細 |
| `us_stock/us_prices.json` | 美股報價快取 |
| `stock/market_status.json` | 市場狀態 |

## R2 寫入對照表

| R2 Key | 來源 |
|--------|------|
| `tmp/weather.json` | CWA + Open-Meteo |
| `assets/esp32_portfolio.json` | gen_esp32_portfolio.py |
| `assets/portfolio_data.json` | gen_portfolio_data.py |
| `assets/dividend_data.json` | update_dividend_data.py |
| `stock/index.html` | gen-stock-html.py |
| `taiwan_stocks.json` | fetch-stock-prices.py |
| `us_stocks.json` | update_us_stocks.py |
| `exchange_rate.json` | scrape_taiwan_bank_rate.py |
| `stock/market_status.json` | update_market_status.py |

## 同步策略

建議：
- `taiwan_stocks.json` / `us_stocks.json`：每週從 VM 或 R2 同步一次（持股不會天天變）
- `us_prices.json`：從 Finnhub 每次重新抓，不需同步
