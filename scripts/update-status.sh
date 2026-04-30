#!/bin/bash
# update-status.sh - 只更新系統狀態頁面（bake + 上傳 R2）
WORKSPACE="/home/jhe/.openclaw/workspace"
echo "🔄 資料更新中..."

# Bake + 上傳 R2
bash "$WORKSPACE/scripts/bake-status-page.sh"

echo "✅ 完成（僅 R2）"
