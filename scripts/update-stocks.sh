#!/bin/bash
# update-stocks.sh - 全自動持股更新：抓股價 → 生成 HTML → 上傳 R2
set -e
WORKSPACE="/home/jhe/.openclaw/workspace"
NOW=$(TZ='Asia/Taipei' date '+%Y-%m-%d %H:%M:%S')
echo "🔄 持股更新中... ($NOW)"

# 1. 抓最新股價
echo "📈 抓取股價..."
python3 "$WORKSPACE/scripts/fetch-stock-prices.py"

# 2. 生成 HTML
echo "📊 生成持股總攬..."
python3 "$WORKSPACE/scripts/gen-stock-html.py"

# 3. 上傳 R2（持股總攬 + 行動版）
python3 << 'PYEOF'
import boto3
s3 = boto3.client('s3', endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
    aws_access_key_id='R2_ACCESS_KEY_REDACTED',
    aws_secret_access_key='R2_SECRET_KEY_REDACTED')
s3.upload_file('/home/jhe/.openclaw/workspace/stock/index.html', 'shared-files', 'stock/index.html', ExtraArgs={'ContentType':'text/html'})
print('R2 stock/index.html OK')
PYEOF

echo "✅ 持股更新完成 ($NOW)"