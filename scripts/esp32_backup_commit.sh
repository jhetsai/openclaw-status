#!/usr/bin/env bash
# esp32_backup_commit.sh
# 功能：燒錄完成後自動 commit 程式碼 + 備份韌體
# 用法：bash esp32_backup_commit.sh [description]
# 範例：bash esp32_backup_commit.sh "Weather page: 2x2 forecast grid layout"

set -e

# ===== 參數 =====
PROJECT_DIR="/home/jhe/.openclaw/workspace/esp32-rlcd-project/02_Example/ESP32-S3-Touch-LCD-4.3B"
BACKUP_BASE="/home/jhe/.openclaw/workspace/backups"
BINARY_PATH="$PROJECT_DIR/build/xiaozhi.bin"
SRC_FILE="$PROJECT_DIR/main/application_portfolio.cc"

DESCRIPTION="${1:-"No description provided"}"
TIMESTAMP=$(date +%Y-%m-%d_%H%M)
TODAY=$(date +%Y-%m-%d)
BACKUP_DIR="$BACKUP_BASE/$TODAY/esp32_$(date +%H%M)"

# ===== 檢查專案目錄 =====
if [[ ! -d "$PROJECT_DIR" ]]; then
    echo "❌ 錯誤：專案目錄不存在: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

# ===== 1. 確認有變更需要 commit =====
if git diff --quiet && git diff --cached --quiet; then
    echo "📝 沒有變更需要 commit"
else
    echo "📝 發現變更，正在 commit..."
    
    # 自動 stage 所有變更
    git add -A
    
    # 建立 commit message
    COMMIT_MSG="[$TIMESTAMP] $DESCRIPTION

日期: $TODAY
時間: $(date +%H:%M:%S)

變更說明:
$DESCRIPTION

韌體位置: $BACKUP_DIR/xiaozhi.bin
Binary 大小: $(du -h "$BINARY_PATH" 2>/dev/null | cut -f1 || echo 'N/A')
"
    
    # Commit（失敗不中斷）
    if git commit -m "$COMMIT_MSG"; then
        echo "✅ Commit 完成: $(git rev-parse --short HEAD)"
    else
        echo "⚠️  Commit 失敗（可能沒有變更）"
    fi
fi

# ===== 2. 備份韌體 =====
echo ""
echo "💾 備份韌體..."

# 嘗試讀取 binary 大小
if [[ -f "$BINARY_PATH" ]]; then
    BIN_SIZE=$(du -h "$BINARY_PATH" 2>/dev/null | cut -f1)
    echo "   Binary: $BINARY_PATH ($BIN_SIZE)"
else
    echo "⚠️  Binary 不存在: $BINARY_PATH"
fi

# 建立備份目錄
mkdir -p "$BACKUP_DIR"
echo "   備份目錄: $BACKUP_DIR"

# 複製 source
if [[ -f "$SRC_FILE" ]]; then
    cp "$SRC_FILE" "$BACKUP_DIR/"
    echo "   ✅ Source: $(basename $SRC_FILE)"
fi

# 複製 binary
if [[ -f "$BINARY_PATH" ]]; then
    cp "$BINARY_PATH" "$BACKUP_DIR/"
    echo "   ✅ Binary: $(basename $BINARY_PATH)"
fi

# 如果有 partition table 和 bootloader 也一併備份
PARTITION="$PROJECT_DIR/build/partition_table/partition-table.bin"
BOOTLOADER="$PROJECT_DIR/build/bootloader/bootloader.bin"
if [[ -f "$PARTITION" ]]; then
    cp "$PARTITION" "$BACKUP_DIR/"
    echo "   ✅ Partition table"
fi
if [[ -f "$BOOTLOADER" ]]; then
    cp "$BOOTLOADER" "$BACKUP_DIR/"
    echo "   ✅ Bootloader"
fi

echo ""
echo "📁 備份內容:"
ls -lh "$BACKUP_DIR/" 2>/dev/null | tail -n +2 || echo "   (目錄為空或不存在)"

echo ""
echo "========================================"
echo "✅ 完成！"
echo "   Commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'N/A')"
echo "   備份:   $BACKUP_DIR"
echo "========================================"
