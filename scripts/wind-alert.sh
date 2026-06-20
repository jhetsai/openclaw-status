#!/bin/bash
# wind-alert.sh - 水林鄉風速預報，每次檢查都發通知（不論是否超標）

# 載入 API keys
source ~/.api_keys 2>/dev/null || source /home/jhe/.api_keys 2>/dev/null || true

BOT_TOKEN="${TELEGRAM_BOT_TOKEN}"
CHAT_ID="1181571031"
LOG="/home/jhe/.openclaw/workspace/logs/wind_alert.log"
WEATHER_API_KEY="${WEATHER_API_KEY}"

# 抓天氣資料
WX=$(curl -s "https://api.weatherapi.com/v1/forecast.json?key=${WEATHER_API_KEY}&q=23.71,120.29&days=1&aqi=no&alerts=no")

# 解析最大陣風（未來24h）
MAX_GUST=$(echo "$WX" | python3 -c "
import sys, json
d = json.load(sys.stdin)
hours = d['forecast']['forecastday'][0]['hour']
max_gust = max(h['gust_kph'] for h in hours)
print(f'{max_gust:.1f}')
")

# 解析當前陣風
NOW_GUST=$(echo "$WX" | python3 -c "
import sys, json
d = json.load(sys.stdin)
current = d['current']['gust_kph']
print(f'{current:.1f}')
")

WMAX_INT=$(echo "$MAX_GUST" | python3 -c "print(int(float(input().strip())))")

# 寫 log
echo "[$(date '+%Y-%m-%d %H:%M')] 當前陣風: ${NOW_GUST} km/h | 未來24h最高: ${MAX_GUST} km/h" >> "$LOG"

# 組合訊息內容
if [ "$WMAX_INT" -ge 20 ]; then
    TEXT_RAW="⚠️ 風速警示：水林
🌬️ 當前風速：${NOW_GUST} km/h
📈 未來24h最高：${MAX_GUST} km/h"
else
    TEXT_RAW="🌬️ 水林風速報告
🌡️ 當前風速：${NOW_GUST} km/h
📈 未來24h最高：${MAX_GUST} km/h"
fi

# URL encode 中文（處理多行換行）
TEXT=$(python3 -c "
import urllib.parse, sys
msg = '''$TEXT_RAW'''
print(urllib.parse.quote(msg))
")

# 發送 Telegram 並檢查結果
RESP=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage?chat_id=${CHAT_ID}&text=${TEXT}")
echo "[$(date '+%Y-%m-%d %H:%M:%S')] TG response: $RESP" >> "$LOG"

if echo "$RESP" | grep -q '"ok":true'; then
    echo "  -> 已發送通知（${MAX_GUST} km/h）✅" >> "$LOG"
else
    echo "  -> 發送失敗: $RESP" >> "$LOG"
fi