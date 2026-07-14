#!/bin/bash
# JHE Cron Backup 容器驗證腳本
# 用途：NAS 部署後一鍵驗證所有環節

set +e  # 不要因為單一測試失敗就退出

CONTAINER="jhe-cron-backup"

echo "============================================"
echo "  JHE Cron Backup 容器驗證"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"

# === 1. 容器狀態 ===
echo ""
echo "=== [1] 容器狀態 ==="
docker ps --filter "name=$CONTAINER" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
if ! docker ps --filter "name=$CONTAINER" --format "{{.Names}}" | grep -q "$CONTAINER"; then
    echo "❌ 容器未運行！先 docker start $CONTAINER"
    exit 1
fi
echo "✅ 容器在運行"

# === 2. 映像檔 ===
echo ""
echo "=== [2] 映像檔 ==="
docker images | grep jhe-cron || echo "❌ 找不到 jhe-cron 映像檔"

# === 3. Mount 路徑 ===
echo ""
echo "=== [3] Mount 路徑 ==="
docker inspect $CONTAINER --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'

# === 4. Scripts 可讀 ===
echo ""
echo "=== [4] Scripts 可讀 ==="
SCRIPTS_COUNT=$(docker exec $CONTAINER ls /app/scripts/ 2>/dev/null | wc -l)
if [ "$SCRIPTS_COUNT" -lt 5 ]; then
    echo "❌ Scripts 找不到 (只有 $SCRIPTS_COUNT 個)"
    echo "   檢查 mount 路徑是否正確"
else
    echo "✅ 找到 $SCRIPTS_COUNT 個 scripts"
    docker exec $CONTAINER ls /app/scripts/ | head -5
fi

# === 5. Cron 進程 ===
echo ""
echo "=== [5] Cron 進程 ==="
PROC_COUNT=$(docker exec $CONTAINER sh -c 'ls /proc/ 2>/dev/null | grep -E "^[0-9]+$" | wc -l' 2>/dev/null)
if [ -z "$PROC_COUNT" ] || [ "$PROC_COUNT" -lt 3 ]; then
    echo "❌ 容器內進程過少（$PROC_COUNT），可能 cron 沒啟動"
else
    echo "✅ 容器內有 $PROC_COUNT 個進程"
fi

# === 6. Cron 設定 ===
echo ""
echo "=== [6] Cron 設定檔 ==="
CRON_FILE=$(docker exec $CONTAINER ls /etc/cron.d/ 2>/dev/null)
if echo "$CRON_FILE" | grep -q "jhe-cron"; then
    echo "✅ 找到 cron 設定：$CRON_FILE"
else
    echo "❌ cron 設定檔未掛入"
fi

# === 7. 環境變數 ===
echo ""
echo "=== [7] API Keys 環境變數 ==="
ENV_CHECK=$(docker exec $CONTAINER sh -c 'env | grep -E "R2_ACCESS_KEY|FINNHUB_KEY|WEATHER_API_KEY" | wc -l' 2>/dev/null)
if [ "$ENV_CHECK" -lt 3 ]; then
    echo "⚠️  部分 API keys 缺失（$ENV_CHECK/3）"
else
    echo "✅ $ENV_CHECK 個 API keys 已注入"
fi

# === 8. R2 連線 ===
echo ""
echo "=== [8] R2 連線測試 ==="
docker exec $CONTAINER python3 -c "
import boto3
keys = {}
with open('/root/.api_keys') as f:
    for line in f:
        line = line.strip()
        if '=' in line:
            k, v = line.split('=', 1)
            keys[k.strip()] = v.strip()
s3 = boto3.client('s3',
    endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
    aws_access_key_id=keys.get('R2_ACCESS_KEY',''),
    aws_secret_access_key=keys.get('R2_SECRET_KEY',''),
    region_name='auto')
try:
    resp = s3.list_objects_v2(Bucket='shared-files', MaxKeys=1)
    print('✅ R2 連線成功')
except Exception as e:
    print(f'❌ R2 連線失敗: {str(e)[:80]}')
" 2>&1 | tail -3

# === 9. 手動跑 weather 更新 ===
echo ""
echo "=== [9] 手動執行 weather 更新 ==="
WEATHER_OUT=$(docker exec $CONTAINER python3 /app/scripts/gen_esp32_weather.py 2>&1 | tail -3)
echo "$WEATHER_OUT"
if echo "$WEATHER_OUT" | grep -q "Uploaded"; then
    echo "✅ Weather 任務成功"
else
    echo "⚠️  Weather 任務可能失敗，請看 log"
fi

# === 10. 容器啟動 log（最近 10 行）===
echo ""
echo "=== [10] 容器啟動 log ==="
docker logs $CONTAINER 2>&1 | tail -10

echo ""
echo "============================================"
echo "  驗證完成"
echo "============================================"
