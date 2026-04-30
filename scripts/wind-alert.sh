#!/bin/bash
# wind-alert.sh - 水林鄉風速預報，每次檢查都發通知（不論是否超標）
BOT_TOKEN="TELEGRAM_BOT_TOKEN_REDACTED"
CHAT_ID="1181571031"
LOG="/home/jhe/.openclaw/workspace/logs/wind_alert.log"
WEATHER_API_KEY="WEATHER_API_KEY_REDACTED"

WX=$(curl -s "https://api.weatherapi.com/v1/forecast.json?key=${WEATHER_API_KEY}&q=23.71,120.29&days=1&aqi=no&alerts=no")

MAX_GUST=$(echo "$WX" | python3 -c "
import sys, json
d = json.load(sys.stdin)
hours = d['forecast']['forecastday'][0]['hour']
max_gust = max(h['gust_kph'] for h in hours)
print(f'{max_gust:.1f}')
")

NOW_GUST=$(echo "$WX" | python3 -c "
import sys, json
d = json.load(sys.stdin)
current = d['current']['gust_kph']
print(f'{current:.1f}')
")

WMAX_INT=$(echo "$MAX_GUST" | python3 -c "print(int(float(input().strip())))")

echo "[$(date '+%Y-%m-%d %H:%M')] 當前陣風: ${NOW_GUST} km/h | 未來24h最高: ${MAX_GUST} km/h" >> "$LOG"

if [ "$WMAX_INT" -ge 30 ]; then
    TEXT="⚠️ 風速警示：水林
🌬️ 當前風速：${NOW_GUST} km/h
📈 未來24h最高：${MAX_GUST} km/h"
else
    TEXT="🌬️ 水林風速報告
🌡️ 當前風速：${NOW_GUST} km/h
📈 未來24h最高：${MAX_GUST} km/h"
fi

curl -s "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage?chat_id=${CHAT_ID}&text=${TEXT}" > /dev/null
echo "  -> 已發送通知（${MAX_GUST} km/h）"
