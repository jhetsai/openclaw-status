#!/bin/bash
# jhe-cron Docker Entrypoint - 備援機專用
set -e

WORKSPACE_DIR="${WORKSPACE_DIR:-/home/jhe/.openclaw/workspace}"

# ─── 寫入 API keys ─────────────────────────────────────────────────
python3 << PYEOF
import os

keys = {
    'R2_ACCESS_KEY':  os.environ.get('R2_ACCESS_KEY', ''),
    'R2_SECRET_KEY':  os.environ.get('R2_SECRET_KEY', ''),
    'FINNHUB_KEY':    os.environ.get('FINNHUB_KEY', ''),
    'CWA_API_KEY':    os.environ.get('CWA_API_KEY', ''),
    'WEATHER_API_KEY': os.environ.get('WEATHER_API_KEY', ''),
    'WINDY_KEY':      os.environ.get('WINDY_KEY', ''),
    'WINDY_PWD':      os.environ.get('WINDY_PWD', ''),
}

lines = [f'{k}={v}' for k, v in keys.items()]
with open('/root/.api_keys', 'w') as f:
    f.write('\n'.join(lines) + '\n')

print(f'✅ Wrote {len(keys)} API keys to /root/.api_keys')
PYEOF

# ─── 測試 R2 ──────────────────────────────────────────────────────
echo ""
echo "=== JHE Cron Backup Container ==="
echo "Mode: ${NODE_MODE:-backup}"
echo "Workspace: $WORKSPACE_DIR"
echo "Started: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""

echo "=== 測試 R2 連線 ==="
python3 -c "
import boto3, os

keys = {}
with open('/root/.api_keys') as f:
    for line in f:
        line = line.strip()
        if '=' in line:
            k, v = line.split('=', 1)
            keys[k.strip()] = v.strip()

s3 = boto3.client('s3',
    endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
    aws_access_key_id=keys.get('R2_ACCESS_KEY',''),
    aws_secret_access_key=keys.get('R2_SECRET_KEY',''),
    region_name='auto')

try:
    resp = s3.list_objects_v2(Bucket='shared-files', Prefix='tmp/', MaxKeys=1)
    print('✅ R2 連線成功')
except Exception as e:
    print(f'⚠️  R2 連線失敗: {e}（非致命錯誤，跳過）')
"

# ─── 同步持股資料（從 R2 下載，確保 workspace 有最新持股）─────────────
echo ""
echo "=== 同步持股資料 from R2 ==="
python3 << 'PYEOF'
import boto3, os

keys = {}
with open('/root/.api_keys') as f:
    for line in f:
        line = line.strip()
        if '=' in line:
            k, v = line.split('=', 1)
            keys[k.strip()] = v.strip()

s3 = boto3.client('s3',
    endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
    aws_access_key_id=keys.get('R2_ACCESS_KEY',''),
    aws_secret_access_key=keys.get('R2_SECRET_KEY',''),
    region_name='auto')

workspace = os.environ.get('WORKSPACE_DIR', '/home/jhe/.openclaw/workspace')

files = [
    ('taiwan_stocks.json',          f'{workspace}/taiwan_stock/taiwan_stocks.json'),
    ('us_stocks.json',              f'{workspace}/us_stock/us_stocks.json'),
    ('us_prices.json',              f'{workspace}/us_stock/us_prices.json'),
    ('stock/market_status.json',    f'{workspace}/stock/market_status.json'),
    ('assets/portfolio_data.json',  f'{workspace}/assets/portfolio_data.json'),
]

for r2_key, local_path in files:
    try:
        # 只有本地檔案不存在或大小為 0 時才從 R2 下載
        # 避免覆蓋本地真實資料（dividend_data.json 等）
        need_download = True
        if os.path.exists(local_path):
            size = os.path.getsize(local_path)
            if size > 0:
                need_download = False
                print(f'  ⏭️  {r2_key} (本地已有 {size} bytes，略過)')
        
        if need_download:
            resp = s3.get_object(Bucket='shared-files', Key=r2_key)
            data = resp['Body'].read()
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(data)
            print(f'  ✅ {r2_key} (從 R2 同步，{len(data)} bytes)')
    except Exception as e:
        print(f'  ⚠️  {r2_key}: {str(e)[:60]}')
PYEOF

# ─── 執行初始更新 ──────────────────────────────────────────────────
echo ""
echo "=== 執行初始更新 ==="
cd "$WORKSPACE_DIR"
bash scripts/fetch-weather-to-r2.sh >> /app/logs/weather.log 2>&1 && echo "  ✅ 天氣更新完成" || echo "  ⚠️  天氣更新略過"
bash scripts/cron-stock-update.sh >> /app/logs/cron-stock.log 2>&1 && echo "  ✅ 持股更新完成" || echo "  ⚠️  持股更新略過"

# ─── 啟動 cron ─────────────────────────────────────────────────────
echo ""
echo "=== 啟動 cron ==="

# 確保 logs 目錄存在
mkdir -p /app/logs

# 啟動 cron（前景）
cron

echo ""
echo "=== 容器啟動完成 ==="
echo "Logs: /app/logs/"
echo ""

# 保持前景
sleep infinity
