#!/bin/bash
# backup-workspace.sh - 備份 workspace 重要檔案（修改前自動執行）+ git commit

BACKUP_DIR="$HOME/.openclaw_backups/workspace"
TIMESTAMP=$(date '+%Y-%m-%d_%H%M%S')
WORKSPACE="$HOME/.openclaw/workspace"

mkdir -p "$BACKUP_DIR"
cd "$WORKSPACE"

echo "[$TIMESTAMP] Workspace 備份中..."

# Git commit 備份
git add .
git commit -m "[backup] $TIMESTAMP" 2>/dev/null && echo "  ✅ Git backup commit" || echo "  ℹ️ No changes to commit"

# 備份 openclaw-status/ 和 dashboard/ 到 tar.gz（保留最近 10 份）
for dir in openclaw-status dashboard; do
    if [ -d "$dir" ]; then
        tar -czf "$BACKUP_DIR/${dir}_${TIMESTAMP}.tar.gz" "$dir/" 2>/dev/null && echo "  ✅ $dir/"
    fi
done

# 清理舊 backup（保留最近 10 份）
for dir in openclaw-status dashboard; do
    ls -t "$BACKUP_DIR"/${dir}_*.tar.gz 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null
done

echo "[$TIMESTAMP] 備份完成"