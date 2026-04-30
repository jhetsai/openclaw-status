#!/bin/bash
# bake-status-page.sh - Bake system status into HTML, upload to R2
set -e
WORKSPACE="/home/jhe/.openclaw/workspace"
R2_HTML="$WORKSPACE/openclaw-status/index.html"
TMP_API="/tmp/status_api.json"
TS=$(date '+%Y-%m-%d_%H%M%S')

# Load API keys from ~/.api_keys
if [ -f ~/.api_keys ]; then
    set -a
    source ~/.api_keys
    set +a
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bake 系統狀態頁面..."

# fetch system api
curl -sf --max-time 15 "http://localhost:3838/api/status" > "$TMP_API" || echo '{}' > "$TMP_API"

# bake into HTML (weather fetched by Python inside the script)
python3 "$WORKSPACE/scripts/bake-status-page.py" "$R2_HTML" "$TMP_API"

# Upload to R2 with versioned backup
python3 - "$R2_HTML" << 'PYEOF2'
import sys, boto3, datetime, os
html_path = sys.argv[1]
ACCESS_KEY = os.environ.get('R2_ACCESS_KEY')
SECRET_KEY = os.environ.get('R2_SECRET_KEY')
s3 = boto3.client('s3', endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
    aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

with open(html_path) as f:
    content = f.read()

# Try to download current R2 version as backup
try:
    obj = s3.get_object(Bucket='shared-files', Key='openclaw-status/index.html')
    current = obj['Body'].read()
    # Save as timestamped backup
    ts = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
    backup_key = f'openclaw-status/backups/{ts}_index.html'
    s3.put_object(Bucket='shared-files', Key=backup_key,
        Body=current, ContentType='text/html')
    print(f'Backup saved: {backup_key}')
except Exception as e:
    print(f'No previous version to backup: {e}')

# Upload new version
s3.put_object(Bucket='shared-files', Key='openclaw-status/index.html',
    Body=content.encode('utf-8'), ContentType='text/html',
    CacheControl='max-age=300')
print('R2 OK')
PYEOF2

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 完成（僅 R2）"