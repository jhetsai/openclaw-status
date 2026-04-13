#!/bin/bash
# bake-status-page.sh - 把系統狀態 bake 進 HTML 再上傳 R2
set -e
WORKSPACE="/home/jhe/.openclaw/workspace"
R2_HTML="$WORKSPACE/openclaw_status/index.html"
TMP_API="/tmp/status_api.json"
TMP_WX="/tmp/weather_api.json"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bake 系統狀態頁面..."

# 1. fetch system api
curl -sf "http://localhost:3838/api/status" > "$TMP_API" || echo '{}' > "$TMP_API"

# 2. fetch weather
curl -sf "https://api.open-meteo.com/v1/forecast?latitude=23.71&longitude=120.29&current=temperature_2m,weathercode,windspeed_10m&timezone=Asia%2FTaipei" > "$TMP_WX" || echo '{}' > "$TMP_WX"

# 3. bake into HTML (TS 由 Python 取現在時間)
python3 "$WORKSPACE/scripts/bake-status-page.py" "$R2_HTML" "$TMP_API" "$TMP_WX"

# 4. Upload to R2
python3 - "$R2_HTML" << 'PYEOF2'
import sys, boto3
html_path = sys.argv[1]
ACCESS_KEY = 'R2_ACCESS_KEY_REDACTED'
SECRET_KEY = 'R2_SECRET_KEY_REDACTED'
s3 = boto3.client('s3', endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
    aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
with open(html_path) as f:
    content = f.read()
s3.put_object(Bucket='shared-files', Key='openclaw-status/index.html',
    Body=content.encode('utf-8'), ContentType='text/html',
    CacheControl='max-age=300')
print('R2 OK')
PYEOF2

# 5. Push to GitHub
CLONE_DIR="/tmp/openclaw-status-clone"
if [ ! -d "$CLONE_DIR/.git" ]; then
    git clone https://x-access-token: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@github.com/jhetsai/openclaw-status.git "$CLONE_DIR" 2>/dev/null
fi
cp "$R2_HTML" "$CLONE_DIR/index.html"
cd "$CLONE_DIR"
git add index.html
git commit -m "Update: $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null
git push origin main 2>&1 | tail -2
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 完成"
