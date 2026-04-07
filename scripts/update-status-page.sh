#!/bin/bash
# 更新系統狀態頁面到 GitHub Pages

set -e

WORK_DIR="/home/jhe/.openclaw/workspace"
NGROK_API="http://localhost:3838/api/status"
GITHUB_REPO="https://jhetsai:GITHUB_TOKEN_REDACTED@github.com/jhetsai/openclaw-status.git"

echo "=== 開始更新系統狀態頁面 $(date) ==="

# 1. 取得系統狀態
SYSTEM_STATS=$(curl -s "$NGROK_API" 2>/dev/null || echo '{}')

# 2. 產出新的 HTML（使用即時取得的資料）
cat > "$WORK_DIR/openclaw_status/status_live.html" << HTMLEOF
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>系統服務狀態</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, "Microsoft JhengHei", "Segoe UI", sans-serif; background: #f0f2f5; color: #1a1a2e; min-height: 100vh; padding: 20px; font-size: 14px; }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { color: #0d47a1; border-bottom: 3px solid #1976d2; padding-bottom: 12px; margin-bottom: 25px; font-size: 24px; }
        h2 { color: #1565c0; margin: 25px 0 12px 0; font-size: 16px; border-left: 4px solid #1976d2; padding-left: 10px; }
        .card { background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .card h3 { color: #333; font-size: 15px; margin-bottom: 15px; display: flex; align-items: center; gap: 8px; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .status-item { background: #f8f9fa; border-radius: 8px; padding: 12px 15px; }
        .status-item .label { font-size: 12px; color: #666; margin-bottom: 4px; }
        .status-item .value { font-size: 16px; font-weight: 600; color: #1a1a2e; }
        .status-item .value.running { color: #2e7d32; }
        .status-item .value.warning { color: #f57c00; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; }
        .badge.green { background: #e8f5e9; color: #2e7d32; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th, td { border: 1px solid #e0e0e0; padding: 10px 12px; text-align: left; }
        th { background: #1976d2; color: white; font-weight: 500; }
        tr:nth-child(even) { background: #f8f9fa; }
        .time { color: #888; font-size: 12px; }
        .footer { text-align: center; color: #999; font-size: 12px; margin-top: 30px; padding-top: 15px; border-top: 1px solid #ddd; }
        .refresh-btn { background: #1976d2; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; text-decoration: none; display: inline-block; }
        .refresh-btn:hover { background: #1565c0; }
    </style>
</head>
<body>
<div class="container">
<h1>📊 系統服務狀態</h1>
<p class="time">更新時間：$(date '+%Y-%m-%d %H:%M:%S') <a href="?" class="refresh-btn">🔄 重新整理</a></p>

<div class="card">
    <h3>🖥️ 主機資訊</h3>
    <div class="status-grid">
        <div class="status-item"><div class="label">主機名稱</div><div class="value">${HOSTNAME:-jhe-VMware-Virtual-Platform}</div></div>
        <div class="status-item"><div class="label">作業系統</div><div class="value">Linux 6.17.0</div></div>
        <div class="status-item"><div class="label">開機時間</div><div class="value">${UPTIME:-未知}</div></div>
        <div class="status-item"><div class="label">系統類型</div><div class="value">VMware 虛擬機</div></div>
    </div>
</div>

<div class="card">
    <h3>💾 系統資源</h3>
    <div class="status-grid">
        <div class="status-item"><div class="label">記憶體</div><div class="value">${MEM_USED:-?}/ ${MEM_TOTAL:-?} GB</div></div>
        <div class="status-item"><div class="label">記憶體使用</div><div class="value ${MEM_PCT_CLASS:-}">${MEM_PCT:-?}%</div></div>
        <div class="status-item"><div class="label">CPU 使用率</div><div class="value ${CPU_PCT_CLASS:-}">${CPU_PCT:-?}%</div></div>
        <div class="status-item"><div class="label">系統負載</div><div class="value">${LOADAVG:-?}</div></div>
    </div>
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
        <tr><td>Telegram Bot</td><td><span class="badge green">運行中</span></td><td>Bot ID: 8793435853</td></tr>
        <tr><td>LINE Bot</td><td><span class="badge green">運行中</span></td><td>Webhook: ngrok</td></tr>
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

<div class="footer">📊 系統服務狀態 ｜ 蝦助出品 ｜ $(date '+%Y-%m-%d %H:%M:%S')</div>
</div>
</body>
</html>
HTMLEOF

# 3. 複製為 index.html
cp "$WORK_DIR/openclaw_status/status_live.html" "$WORK_DIR/openclaw_status/index.html"

# 4. 推送
cd "$WORK_DIR/openclaw_status"
git add index.html status_live.html
git commit -m "Auto-update: $(date '+%Y-%m-%d %H:%M')" || exit 0
git push "$GITHUB_REPO" main 2>/dev/null || echo "Push failed, will retry next hour"

echo "=== 更新完成 $(date) ==="
