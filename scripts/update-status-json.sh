#!/bin/bash
# update-status-json.sh - 更新 R2 上的系統狀態 JSON + HTML
# 由心跳 cron 呼叫

STATUS_API="http://localhost:3838/api/status"
TS=$(TZ='Asia/Taipei' date '+%Y-%m-%d %H:%M:%S')
WORKSPACE="/home/jhe/.openclaw/workspace"
R2_HTML="$WORKSPACE/openclaw-status/index.html"
TMP_JSON="/tmp/openclaw_status.json"

# 1. 抓 API 寫入 JSON
curl -s "$STATUS_API" > "$TMP_JSON"

if [ $? -eq 0 ]; then
    python3 - "$TMP_JSON" "$TS" << 'PYEOF'
import sys, json, boto3
fpath, ts = sys.argv[1], sys.argv[2]
with open(fpath) as f:
    d = json.load(f)
d['ts'] = ts

ACCESS_KEY = os.environ.get('R2_ACCESS_KEY')
SECRET_KEY = os.environ.get('R2_SECRET_KEY')
s3 = boto3.client('s3', endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
    aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

# 上傳 JSON
s3.put_object(Bucket='shared-files', Key='openclaw-status/status.json',
    Body=json.dumps(d, ensure_ascii=False, indent=2),
    ContentType='application/json')

# 更新 HTML 裡的 JS 變數（bake-in 方式）
R2_HTML = '/home/jhe/.openclaw/workspace/openclaw-status/index.html'
with open(R2_HTML) as f:
    content = f.read()

# 將 fetch JSON 拿掉，改成直接用 bake-in 的變數
# 在 fetch().then() 之前，先把 d 設好
content = content.replace(
    "fetch('https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/openclaw-status/status.json')",
    "Promise.resolve(null)"
)

# 在 .then(function(d){ 之前插入 bake-in 資料
content = content.replace(
    ".then(function(d){",
    "var _baked = " + json.dumps(d, ensure_ascii=False) + "; d = _baked;\n    .then(function(d){"
)

# 更新版本時間
content = content.replace(
    "var ts = d.ts || '2026-04-11 16:00:48';",
    "var ts = '" + ts + "';"
)

with open(R2_HTML, 'w') as f:
    f.write(content)
print('HTML updated + JSON uploaded OK')
PYEOF
else
    echo "API fetch failed"
fi
