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
python3 - "$WORKSPACE/stock_portfolio.html" "stock/index.html" << 'PYEOF'
import sys, boto3
src, dst = sys.argv[1], sys.argv[2]
KEYS = 'R2_ACCESS_KEY_REDACTED'
SECT = 'R2_SECRET_KEY_REDACTED'
s3 = boto3.client('s3', endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
    aws_access_key_id=KEYS, aws_secret_access_key=SECT)
s3.upload_file(src, 'shared-files', dst, ExtraArgs={'ContentType':'text/html'})
print('✅ stock/index.html')
PYEOF

python3 - "$WORKSPACE/stock/mobile.html" "stock/mobile.html" << 'PYEOF'
import sys, boto3
src, dst = sys.argv[1], sys.argv[2]
KEYS = 'R2_ACCESS_KEY_REDACTED'
SECT = 'R2_SECRET_KEY_REDACTED'
s3 = boto3.client('s3', endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
    aws_access_key_id=KEYS, aws_secret_access_key=SECT)
s3.upload_file(src, 'shared-files', dst, ExtraArgs={'ContentType':'text/html'})
print('✅ stock/mobile.html')
PYEOF

echo "✅ 持股更新完成 ($NOW)"

# 4. 上傳 GitHub（stock repo）
cp "$WORKSPACE/stock_portfolio.html" /tmp/stock-clone/index.html
cp "$WORKSPACE/stock/mobile.html" /tmp/stock-clone/mobile.html
cd /tmp/stock-clone && git add index.html mobile.html && git commit -m "Update: $(date '+%H:%M:%S')" && git push origin main 2>&1 | tail -2
