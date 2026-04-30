#!/bin/bash
set -e

WORK_DIR="/tmp/openclaw-status-page"
STATUS_API="http://localhost:3838/api/status"

echo "[$(date '+%H:%M:%S')] 更新系統狀態頁面..."

# 取得系統狀態
STATS=$(curl -s "$STATUS_API" 2>/dev/null || echo '{}')

HOSTNAME=$(echo "$STATS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('hostname','jhe-VMware'))" 2>/dev/null || echo "jhe")
UPTIME=$(echo "$STATS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('uptime','?'))" 2>/dev/null || echo "?")
MEM_TOTAL=$(echo "$STATS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('memTotal','?'))" 2>/dev/null || echo "?")
MEM_USED=$(echo "$STATS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('memUsed','?'))" 2>/dev/null || echo "?")
MEM_PCT=$(echo "$STATS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('memPercent','?'))" 2>/dev/null || echo "?")
CPU_PCT=$(echo "$STATS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('cpuPercent','?'))" 2>/dev/null || echo "?")
LOADAVG=$(echo "$STATS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(' / '.join(d.get('loadavg',['?','?','?'])))" 2>/dev/null || echo "?")

[ "${MEM_PCT%.*}" -gt 80 ] 2>/dev/null && MEM_PCT_CLASS="warning" || MEM_PCT_CLASS=""
[ "${CPU_PCT%.*}" -gt 80 ] 2>/dev/null && CPU_PCT_CLASS="warning" || CPU_PCT_CLASS=""

cat > "$WORK_DIR/index.html" << 'HTMLEOF'
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>系統服務狀態</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, "Microsoft JhengHei", sans-serif; background: #f0f2f5; color: #1a1a2e; min-height: 100vh; padding: 20px; font-size: 14px; }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { color: #0d47a1; border-bottom: 3px solid #1976d2; padding-bottom: 12px; margin-bottom: 25px; font-size: 24px; }
        .card { background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .card h3 { color: #333; font-size: 15px; margin-bottom: 15px; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .status-item { background: #f8f9fa; border-radius: 8px; padding: 12px 15px; }
        .status-item .label { font-size: 12px; color: #666; margin-bottom: 4px; }
        .status-item .value { font-size: 16px; font-weight: 600; }
        .status-item .value.running { color: #2e7d32; }
        .status-item .value.warning { color: #f57c00; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; background: #e8f5e9; color: #2e7d32; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th, td { border: 1px solid #e0e0e0; padding: 10px 12px; text-align: left; }
        th { background: #1976d2; color: white; }
        tr:nth-child(even) { background: #f8f9fa; }
        .time { color: #888; font-size: 12px; }
        .footer { text-align: center; color: #999; font-size: 12px; margin-top: 30px; padding-top: 15px; border-top: 1px solid #ddd; }
        .refresh-btn { background: #1976d2; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; text-decoration: none; display: inline-block; }
        .refresh-btn:hover { background: #1565c0; }
        a { color: #1976d2; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
<div class="container">
<h1>📊 系統服務狀態</h1>
<p class="time">更新時間：REPLACETIME <a href="?" class="refresh-btn">🔄 重新整理</a></p>

<div class="card">
    <h3>🖥️ 主機資訊</h3>
    <div class="status-grid">
        <div class="status-item"><div class="label">主機名稱</div><div class="value">REPLACEHOSTNAME</div></div>
        <div class="status-item"><div class="label">作業系統</div><div class="value">Linux 6.17.0</div></div>
        <div class="status-item"><div class="label">開機時間</div><div class="value">REPLACEUPTIME</div></div>
        <div class="status-item"><div class="label">系統類型</div><div class="value">VMware 虛擬機</div></div>
    </div>
</div>

<div class="card">
    <h3>💾 系統資源</h3>
    <div class="status-grid">
        <div class="status-item"><div class="label">記憶體</div><div class="value">REPLACEMEMUSED / REPLACEMEMTOTAL GB</div></div>
        <div class="status-item"><div class="label">記憶體使用</div><div class="value REPLACEMEMCLASS">REPLACEMEMPCT%</div></div>
        <div class="status-item"><div class="label">CPU 使用率</div><div class="value REPLACECPUCLASS">REPLACECPUPCT%</div></div>
        <div class="status-item"><div class="label">系統負載</div><div class="value">REPLACELOADAVG</div></div>
    </div>
</div>

<div class="card">
    <h3>🔗 線上服務連結</h3>
    <table>
        <tr><th>服務</th><th>連結</th><th>說明</th></tr>
        <tr><td>📦 庫存系統</td><td>R2</td><td>LINE 照片上傳庫存盤點</td></tr>
        <tr><td>📊 系統狀態</td><td>R2</td><td>每小時自動更新</td></tr>
        <tr><td>🌾 農田天氣</td><td>R2</td><td>農田氣象資訊</td></tr>
        <tr><td>⚡ 台電系統</td><td>R2</td><td>台電電費查詢</td></tr>
    </table>
</div>

<div class="card">
    <h3>🚀 OpenClaw 服務</h3>
    <div class="status-grid">
        <div class="status-item"><div class="label">Gateway 狀態</div><div class="value running">✅ 運行中</div></div>
        <div class="status-item"><div class="label">Gateway PID</div><div class="value">117323</div></div>
        <div class="status-item"><div class="label">Node.js 版本</div><div class="value">v22.22.0</div></div>
        <div class="status-item"><div class="label">目前模型</div><div class="value">MiniMax M2.7</div></div>
    </div>
</div>

<div class="card">
    <h3>📱 通訊服務</h3>
    <table>
        <tr><th>服務</th><th>狀態</th><th>說明</th></tr>
        <tr><td>Telegram Bot</td><td><span class="badge">運行中</span></td><td>Bot ID: 8793435853</td></tr>
        <tr><td>LINE Bot</td><td><span class="badge">運行中</span></td><td>Webhook: ngrok</td></tr>
    </table>
</div>

<div class="card">
    <h3>⏰ 排程任務（共 7 個）</h3>
    <table>
        <tr><th>任務</th><th>時間</th><th>說明</th></tr>
        <tr><td>每日晨間新聞簡報</td><td>06:00</td><td>直接執行</td></tr>
        <tr><td>每日美股損益報告</td><td>08:30</td><td>需確認</td></tr>
        <tr><td>每日台股損益報告</td><td>14:00</td><td>需確認</td></tr>
        <tr><td>每日系統備份報告</td><td>19:00</td><td>需確認</td></tr>
        <tr><td>定時記憶存檔</td><td>12:00, 18:00</td><td>需確認</td></tr>
        <tr><td>多使用者記憶存檔</td><td>12:00, 18:00</td><td>需確認</td></tr>
        <tr><td>風速監測警示</td><td>08:00, 12:00, 18:00</td><td>直接執行</td></tr>
    </table>
</div>

<div class="card">
    <h3>🔍 API 與工具</h3>
    <table>
        <tr><th>服務</th><th>用途</th><th>月用量</th></tr>
        <tr><td>Brave Search</td><td>網路搜尋</td><td>55 / 1,000</td></tr>
        <tr><td>MiniMax M2.7</td><td>AI 模型</td><td>Starter</td></tr>
        <tr><td>Leonardo.ai</td><td>圖像生成</td><td>150 張/天</td></tr>
    </table>
</div>

<div class="footer">📊 系統服務狀態 ｜ 蝦助出品 ｜ REPLACEFOOTERTIME</div>
</div>
</body>
</html>
HTMLEOF

# Replace placeholders
sed -i "s|REPLACETIME|$(date '+%Y-%m-%d %H:%M:%S')|g" "$WORK_DIR/index.html"
sed -i "s|REPLACEHOSTNAME|$HOSTNAME|g" "$WORK_DIR/index.html"
sed -i "s|REPLACEUPTIME|$UPTIME|g" "$WORK_DIR/index.html"
sed -i "s|REPLACEMEMTOTAL|$MEM_TOTAL|g" "$WORK_DIR/index.html"
sed -i "s|REPLACEMEMUSED|$MEM_USED|g" "$WORK_DIR/index.html"
sed -i "s|REPLACEMEMPCT|$MEM_PCT|g" "$WORK_DIR/index.html"
sed -i "s|REPLACEMEMCLASS|$MEM_PCT_CLASS|g" "$WORK_DIR/index.html"
sed -i "s|REPLACECPUPCT|$CPU_PCT|g" "$WORK_DIR/index.html"
sed -i "s|REPLACECPUCLASS|$CPU_PCT_CLASS|g" "$WORK_DIR/index.html"
sed -i "s|REPLACELOADAVG|$LOADAVG|g" "$WORK_DIR/index.html"
sed -i "s|REPLACEFOOTERTIME|$(date '+%Y-%m-%d %H:%M:%S')|g" "$WORK_DIR/index.html"



echo "[$(date '+%H:%M:%S')] 更新完成"

# Also upload raw JSON to R2 for the R2 status page
curl -s "http://localhost:3838/api/status" | python3 -c "
import sys, json
d = json.load(sys.stdin)
d['ts'] = '$(TZ=Asia/Taipei date "+%Y-%m-%d %H:%M:%S")'
print(json.dumps(d))
" > /tmp/openclaw_status.json

python3 - "$WORK_DIR/index.html" << 'PYEOF'
import sys, json, boto3

ACCESS_KEY = os.environ.get('R2_ACCESS_KEY')
SECRET_KEY = os.environ.get('R2_SECRET_KEY')
s3 = boto3.client('s3', endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
    aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

# Upload JSON
with open('/tmp/openclaw_status.json') as f:
    data = json.load(f)
    data['ts'] = '$(TZ=Asia/Taipei date "+%Y-%m-%d %H:%M:%S")'
s3.put_object(Bucket='shared-files', Key='openclaw-status/status.json',
    Body=json.dumps(data, ensure_ascii=False),
    ContentType='application/json')
print('JSON uploaded')
PYEOF

# Also upload the baked HTML to R2
python3 - "$WORK_DIR/index.html" << 'PYEOF2'
import sys, boto3, json
html_path = sys.argv[1]
ACCESS_KEY = os.environ.get('R2_ACCESS_KEY')
SECRET_KEY = os.environ.get('R2_SECRET_KEY')
s3 = boto3.client('s3', endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
    aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
with open(html_path) as f:
    content = f.read()
# Remove the problematic fetch from R2 JSON, use bake-in data instead
content = content.replace(
    "fetch('https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/openclaw-status/status.json')",
    "Promise.resolve(null)"
)
# Fix ts to use baked d.ts
content = content.replace(
    "var ts = d.ts || '2026-04-11 16:00:48';",
    "var ts = d ? (d.ts || '-') : '-';"
)
s3.put_object(Bucket='shared-files', Key='openclaw-status/index.html',
    Body=content.encode('utf-8'),
    ContentType='text/html')
print('R2 HTML uploaded')
PYEOF2
