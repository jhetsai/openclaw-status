#!/bin/bash
# 持股自動更新 Cron 脚本
# 每10分鐘執行一次（開盤時段），休市日跳過

WORKSPACE="/home/jhe/.openclaw/workspace"
cd "$WORKSPACE"

# Load API keys
if [ -f ~/.api_keys ]; then
    set -a
    source ~/.api_keys
    set +a
fi

# 檢查是否為休市日
HOLIDAY_CHECK=$(python3 scripts/check_holiday.py)
TW_HOLIDAY=$(echo "$HOLIDAY_CHECK" | python3 -c "import json,sys; d=json.load(sys.stdin); print('yes' if d['tw_holiday'] else 'no')" 2>/dev/null || echo "no")
US_HOLIDAY=$(echo "$HOLIDAY_CHECK" | python3 -c "import json,sys; d=json.load(sys.stdin); print('yes' if d['us_holiday'] else 'no')" 2>/dev/null || echo "no")

# 兩個市場都休市仍更新股價（顯示最後收盤價）
if [ "$TW_HOLIDAY" = "yes" ] && [ "$US_HOLIDAY" = "yes" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 兩市場休市，仍更新最後收盤價" >> logs/cron-stock.log
fi

# 執行持股更新
bash scripts/update-stocks.sh >> logs/cron-stock.log 2>&1

# (add_update_time_tw.py 已由 fetch-stock-prices.py 內含，無需單獨執行)

# 上傳 taiwan_stocks.json 到 R2
python3 scripts/upload_r2.py "$WORKSPACE/taiwan_stock/taiwan_stocks.json" >> logs/cron-stock.log 2>&1

# 同步上傳到根目錄（提供給資產儀表板讀取）
python3 - << 'PYEOF' >> logs/cron-stock.log 2>&1
import boto3, os
s3 = boto3.client('s3', endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
    aws_access_key_id=os.environ.get('R2_ACCESS_KEY'),
    aws_secret_access_key=os.environ.get('R2_SECRET_KEY'))
s3.upload_file('/home/jhe/.openclaw/workspace/taiwan_stock/taiwan_stocks.json', 'shared-files', 'taiwan_stocks.json',
    ExtraArgs={'ContentType':'application/json'})
print('taiwan_stocks.json OK')
PYEOF


# 更新 us_stocks.json 並上傳
python3 scripts/update_us_stocks.py >> logs/cron-stock.log 2>&1
python3 scripts/upload_r2.py "$WORKSPACE/us_stock/us_stocks.json" >> logs/cron-stock.log 2>&1

# 同步上傳 us_stocks.json 到根目錄
python3 - << 'PYEOF' >> logs/cron-stock.log 2>&1
import boto3, os
s3 = boto3.client('s3', endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
    aws_access_key_id=os.environ.get('R2_ACCESS_KEY'),
    aws_secret_access_key=os.environ.get('R2_SECRET_KEY'))
s3.upload_file('/home/jhe/.openclaw/workspace/us_stock/us_stocks.json', 'shared-files', 'us_stocks.json',
    ExtraArgs={'ContentType':'application/json'})
print('us_stocks.json OK')
PYEOF


# 更新並上傳 market_status.json
python3 scripts/update_market_status.py >> logs/cron-stock.log 2>&1
python3 scripts/upload_r2.py "$WORKSPACE/stock/market_status.json" >> logs/cron-stock.log 2>&1

# 更新匯率並上傳到 R2（使用臺灣銀行即期匯率本行買入）
python3 "$WORKSPACE/scripts/scrape_taiwan_bank_rate.py" >> "$WORKSPACE/logs/exchange_rate.log" 2>&1

# 更新 portfolio_data.json（合併股價+配息+匯率為單一資料源）
python3 "$WORKSPACE/scripts/gen_portfolio_data.py" >> "$WORKSPACE/logs/cron-stock.log" 2>&1

echo "Cron stock update completed at $(date '+%Y-%m-%d %H:%M:%S')" >> logs/cron-stock.log
