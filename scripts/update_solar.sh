#!/bin/bash
# 太陽能發電記錄更新 script
# 用法: bash update_solar.sh <累計kWh>
# 例如: bash update_solar.sh 288.8

set -e

CUMULATIVE=$1
if [ -z "$CUMULATIVE" ]; then
  echo "用法: bash update_solar.sh <累計kWh>"
  echo "例如: bash update_solar.sh 288.8"
  exit 1
fi

CSV="/home/jhe/.openclaw/workspace/solar_history.csv"
WORKSPACE="/home/jhe/.openclaw/workspace"
TODAY=$(date +%Y-%m-%d)

# Step 1: 查天氣
echo "[1/4] 查詢天氣..."
WEATHER=$(curl -s "wttr.in/Yunlin?format=j1" | python3 -c "
import sys,json
d=json.load(sys.stdin)
w=d['current_condition'][0]
print(f\"{w['temp_C']},{w['humidity']},{w['windspeedKmph']},{w['weatherDesc'][0]['value'].strip()},{w.get('uvIndex',0)}\")
" 2>/dev/null || echo "28,80,4,Unknown,0")

IFS=',' read -r TEMP HUMIDITY WIND WEATHER_DESC UV <<< "$WEATHER"

# 翻譯天氣描述為中文
case "$WEATHER_DESC" in
  "Partly Cloudy") WEATHER_DESC="局部多雲" ;;
  "Cloudy") WEATHER_DESC="多雲" ;;
  "Overcast") WEATHER_DESC="陰天" ;;
  "Clear") WEATHER_DESC="晴" ;;
  "Sunny") WEATHER_DESC="晴天" ;;
  "Light rain") WEATHER_DESC="小雨" ;;
  "Moderate rain") WEATHER_DESC="中雨" ;;
  "Heavy rain") WEATHER_DESC="大雨" ;;
  "Patchy rain possible") WEATHER_DESC="局部陣雨" ;;
  "Patchy rain nearby") WEATHER_DESC="局部陣雨" ;;
  "Thundery outbreaks possible") WEATHER_DESC="局部雷陣雨" ;;
  "Blowing snow") WEATHER_DESC="吹雪" ;;
  "Blizzard") WEATHER_DESC="暴風雪" ;;
  "Fog") WEATHER_DESC="霧" ;;
  "Freezing fog") WEATHER_DESC="凍霧" ;;
  "Light drizzle") WEATHER_DESC="毛毛雨" ;;
  "Mist") WEATHER_DESC="薄霧" ;;
  "Moderate or heavy rain shower") WEATHER_DESC="陣雨" ;;
  "Light sleet") WEATHER_DESC="小雨夾雪" ;;
  "Light snow") WEATHER_DESC="小雪" ;;
  "Moderate or heavy snow showers") WEATHER_DESC="陣雪" ;;
  "Moderate snow") WEATHER_DESC="中雪" ;;
  "Heavy snow") WEATHER_DESC="大雪" ;;
  "Ice") WEATHER_DESC="結冰" ;;
  "Torrential rain") WEATHER_DESC="豪大雨" ;;
  "Heavy drizzle") WEATHER_DESC="持續毛雨" ;;
  "Light rain shower") WEATHER_DESC="短暫小雨" ;;
esac

echo "  天氣: $WEATHER_DESC, 氣溫: ${TEMP}°C, 濕度: ${HUMIDITY}%, 風速: ${WIND} km/h, UV: $UV"

# Step 2: 讀取上次累計，計算日發電
echo "[2/4] 更新 CSV..."
LAST_LINE=$(tail -1 "$CSV")
LAST_CUM=$(echo "$LAST_LINE" | awk -F',' '{print $2}')
DAILY=$(python3 -c "print(round($CUMULATIVE - $LAST_CUM, 1))")

# 體感溫度
FEELS=$(curl -s "wttr.in/Yunlin?format=j1" | python3 -c "
import sys,json
d=json.load(sys.stdin)
w=d['current_condition'][0]
print(w.get('FeelsLikeC', w['temp_C']))
" 2>/dev/null || echo "$TEMP")

# 寫入 CSV
echo "${TODAY},${CUMULATIVE},${DAILY},${WEATHER_DESC},${UV},${WIND},${TEMP},體感${FEELS}°C,濕度${HUMIDITY}%" >> "$CSV"
echo "  已寫入: ${TODAY},${CUMULATIVE},${DAILY},${WEATHER_DESC}"

# Step 3: 重建 HTML
echo "[3/4] 重建 HTML..."
python3 "${WORKSPACE}/solar/gen_solar_html.py"

# Step 4: 上傳 R2
echo "[4/4] 上傳 R2..."
python3 "${WORKSPACE}/scripts/upload_r2.py" "${WORKSPACE}/solar/index.html"

# 更新 memory
echo "[done] 累積發電: ${CUMULATIVE} kWh, 日發電: ${DAILY} kWh"
