#!/bin/bash
# wind-alert.sh - 檢查水林鄉風速，超過30km/h則發Telegram警示
set -e

BOT_TOKEN="TELEGRAM_BOT_TOKEN_REDACTED"
CHAT_ID="1181571031"
LOG="/home/jhe/.openclaw/workspace/logs/wind_alert.log"

# 抓取風速預報
WX=$(curl -s "https://api.open-meteo.com/v1/forecast?latitude=23.71&longitude=120.29&hourly=wind_speed_10m,wind_gusts_10m&timezone=Asia%2FTaipei&forecast_days=1")

# 取出未來24小時最高風速
MAX_WIND=$(echo "$WX" | python3 -c "
import sys, json
d = json.load(sys.stdin)
hours = d['hourly']
winds = hours['wind_speed_10m'][0:24]  # 未來24小時
gusts = hours['wind_gusts_10m'][0:24]
max_w = max(winds)
max_g = max(gusts)
max_val = max(max_w, max_g)
times = hours['time'][winds.index(max_w)]
print(f'{max_val:.1f}')
")

MAX_WIND_INT=$(echo "$MAX_WIND" | python3 -c "print(int(float(input().strip())))")

echo "[$(date '+%Y-%m-%d %H:%M')] 最高風速: ${MAX_WIND} km/h" >> "$LOG"

if [ "$MAX_WIND_INT" -ge 30 ]; then
    MSG="🚨【水林鄉風速警示】
未來24小時最高風速：${MAX_WIND} km/h
已超過警戒線 30 km/h"
    curl -s -X POST "https://api.telegram.org/${BOT_TOKEN}/sendMessage" \
        -d "chat_id=${CHAT_ID}" \
        -d "text=${MSG}" > /dev/null
    echo "  → 已發送警示" >> "$LOG"
else
    echo "  → 無超標，正常" >> "$LOG"
fi
