#!/bin/bash
# ESP32 天氣資料更新腳本
# 每10分鐘執行一次，更新 R2 上的天氣 JSON
# 供 ESP32-S3-RLCD 離線下載使用

API_KEYS="$HOME/.api_keys"
R2_UPLOAD="$HOME/.openclaw/workspace/scripts/upload_r2.py"
TMP_JSON="/tmp/esp32_weather.json"
R2_PATH="tmp/weather.json"

# 讀取 R2 設定
source "$API_KEYS" 2>/dev/null

# 抓 wttr.in 天氣（備用，不用 API key）
WEATHER_DATA=$(curl -s "wttr.in/Yunlin?format=j1")
TEMP=$(echo "$WEATHER_DATA" | python3 -c "
import sys, json
d = json.load(sys.stdin)
cc = d['current_condition'][0]
print(cc['temp_C'])
")
DESC=$(echo "$WEATHER_DATA" | python3 -c "
import sys, json
d = json.load(sys.stdin)
cc = d['current_condition'][0]
print(cc['weatherDesc'][0]['value'])
")

# 翻譯天氣描述
case "$DESC" in
  *"Clear"*) DESC_CN="晴";;
  *"sunny"*) DESC_CN="晴";;
  *"Partly cloudy"*) DESC_CN="多雲";;
  *"Cloudy"*) DESC_CN="陰";;
  *"Overcast"*) DESC_CN="陰";;
  *"Rain"*) DESC_CN="雨";;
  *"Drizzle"*) DESC_CN="毛毛雨";;
  *"Shower"*) DESC_CN="陣雨";;
  *"Light rain shower"*) DESC_CN="小雨";;
  *"Thunderstorm"*) DESC_CN="雷雨";;
  *"Fog"*) DESC_CN="霧";;
  *"Mist"*) DESC_CN="薄霧";;
  *) DESC_CN="$DESC";;
esac

# 抓 NTP 時間
NTP_TIME=$(date "+%Y-%m-%d %H:%M:%S")
EPOCH=$(date +%s)

# 建立 JSON
cat > "$TMP_JSON" << EOF
{
  "time": "$NTP_TIME",
  "temp": $TEMP,
  "desc": "$DESC_CN",
  "humidity": 80,
  "updated": $EPOCH
}
EOF

# 上傳到 R2
python3 "$R2_UPLOAD" "$TMP_JSON" "$R2_PATH" 2>&1

echo "[$(date)] Updated: ${TEMP}°C $DESC_CN"