#!/bin/bash
# auto-update-all.sh - 自動更新系統狀態頁面
set -e

WORKSPACE_HTML="/home/jhe/.openclaw/workspace/openclaw_status/index.html"
TMP_HTML="/tmp/openclaw-status/index.html"
STATUS_API="http://localhost:3838/api/status"
CWA_API="https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization=CWA_API_KEY_REDACTED&limit=50"
METEO_API="https://api.open-meteo.com/v1/forecast?latitude=23.71&longitude=120.29&current=temperature_2m,weathercode,windspeed_10m&timezone=Asia%2FTaipei"
TOKEN="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"
NOW=$(date '+%Y-%m-%d %H:%M:%S')
NOW_SHORT=$(date '+%H:%M')

echo "=== 自動更新 $NOW ==="

# 1. 抓取 system-api 資料
STATUS_DATA=$(curl -s $STATUS_API 2>/dev/null || echo "{}")

# 2. 抓取 Open-Meteo 氣象（伺服器端）
METEO_DATA=$(curl -s $METEO_API 2>/dev/null || echo "{}")

# 3. 從 workspace 複製乾淨版本到 /tmp
cp "$WORKSPACE_HTML" "$TMP_HTML"

# 4. 用 Python 更新 HTML
python3 - "$TMP_HTML" "$NOW" "$NOW_SHORT" "$STATUS_DATA" "$METEO_DATA" << 'PYEOF'
import sys, json, re

html_path = sys.argv[1]
now = sys.argv[2]
now_short = sys.argv[3]
try:
    status = json.loads(sys.argv[4])
except:
    status = {}
try:
    meteo = json.loads(sys.argv[5])
except:
    meteo = {}

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# === 更新 footer 時間 ===
content = re.sub(
    r'📊 系統服務狀態 ｜ 蝦助出品 ｜ \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',
    f'📊 系統服務狀態 ｜ 蝦助出品 ｜ {now}',
    content
)

# === 更新 <p class="time"> 時間 ===
content = re.sub(
    r'更新時間：\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',
    f'更新時間：{now}',
    content
)

# === 更新系統資訊 ===
def update_value(content, label, new_value):
    pattern = r'(<div class="status-item">.*?<div class="label">' + re.escape(label) + r'</div>.*?<div class="value">)[^<]*(</div>)'
    replacement = r'\g<1>' + new_value + r'\2'
    return re.sub(pattern, replacement, content, flags=re.DOTALL)

uptime = status.get('uptime', '?')
mem_used = status.get('memUsed', '?')
mem_total = status.get('memTotal', '?')
cpu = status.get('cpuPercent', '?')

content = update_value(content, '開機時間', uptime)
content = update_value(content, '記憶體', f'{mem_used} / {mem_total} GB')
content = update_value(content, 'CPU 使用率', f'{cpu}%')

# === 更新 Open-Meteo 氣象資料 ===
try:
    c = meteo.get('current', {})
    temp = c.get('temperature_2m', '?')
    wind = c.get('windspeed_10m', '?')
    code = c.get('weathercode', 0)
    
    wtxt = '晴'
    if code <= 3:
        wtxt = '多雲'
    elif code <= 48:
        wtxt = '霧'
    elif code <= 55:
        wtxt = '毛毛雨'
    elif code <= 65:
        wtxt = '雨'
    elif code <= 75:
        wtxt = '雪'
    else:
        wtxt = '惡劣'
    
    eff = '正常'
    eff_color = '#f57c00'
    if code == 0:
        eff = '高'
        eff_color = '#2e7d32'
    elif code <= 3:
        eff = '正常'
        eff_color = '#f57c00'
    elif code <= 48:
        eff = '偏低'
        eff_color = '#f57c00'
    else:
        eff = '低'
        eff_color = '#c62828'
    
    content = update_value(content, '麥寮測站', f'水林 {wtxt}')
    content = update_value(content, '氣溫', f'{temp}°C')
    content = update_value(content, '風速', f'{wind} km/h')
    content = update_value(content, '今日天氣', wtxt)
    
    # 發電效率需要特殊處理（更新文字+顏色）
    eff_pattern = r'(<div class="status-item">.*?<div class="label">發電效率</div>.*?<div class="value">)[^<]*(</div>)'
    eff_replacement = r'\g<1>' + eff + r'\2'
    content = re.sub(eff_pattern, eff_replacement, content, flags=re.DOTALL)
    
    content = update_value(content, '資料時間', now_short)
    
    print(f"Meteo: {temp}°C, 風速{wind}km/h, {wtxt}, 效率{eff}")
except Exception as e:
    print(f"Meteo error: {e}")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"System: uptime={uptime}, memory={mem_used}/{mem_total}GB, cpu={cpu}%")
PYEOF

# 5. 上传到 R2
python3 << 'PYEOF'
import boto3, urllib.request, json, base64

s3 = boto3.client('s3', endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com', 
    aws_access_key_id='R2_ACCESS_KEY_REDACTED', 
    aws_secret_access_key='R2_SECRET_KEY_REDACTED')
s3.upload_file('/tmp/openclaw-status/index.html', 'shared-files', 'openclaw-status/index.html', 
    ExtraArgs={'ContentType': 'text/html'})
print("R2: OK")
PYEOF

# 6. 上传到 GitHub
python3 << 'PYEOF'
import urllib.request, json, base64

TOKEN = "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"
with open('/tmp/openclaw-status/index.html', 'r', encoding='utf-8') as f:
    content = f.read()
encoded = base64.b64encode(content.encode('utf-8')).decode('ascii')
req = urllib.request.Request('https://api.github.com/repos/jhetsai/openclaw-status/contents/index.html',
    headers={'Authorization': f'token {TOKEN}', 'Accept': 'application/vnd.github.v3+json'})
current = json.loads(urllib.request.urlopen(req).read())
sha = current['sha']
data = json.dumps({'message': 'Update with server-side Meteo fetch', 'content': encoded, 'sha': sha}).encode('utf-8')
req = urllib.request.Request('https://api.github.com/repos/jhetsai/openclaw-status/contents/index.html',
    headers={'Authorization': f'token {TOKEN}', 'Accept': 'application/vnd.github.v3+json', 'Content-Type': 'application/json'},
    data=data, method='PUT')
urllib.request.urlopen(req).read()
print("GitHub: OK")
PYEOF

echo "=== 更新完成 ==="
