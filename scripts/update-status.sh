#!/bin/bash
# update-status.sh - 只更新系統狀態頁面（bake + 上傳 R2 + GitHub）
WORKSPACE="/home/jhe/.openclaw/workspace"
echo "🔄 資料更新中..."

# Bake + 上傳 R2
bash "$WORKSPACE/scripts/bake-status-page.sh"

# 上傳 GitHub
cp "$WORKSPACE/openclaw_status/index.html" /tmp/openclaw/index.html
cd /tmp/openclaw && git add index.html && git commit -m "Bake: $(date '+%H:%M:%S')" && git push origin main 2>&1 | tail -2

echo "✅ 完成"
