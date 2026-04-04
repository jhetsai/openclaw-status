#!/bin/bash
# 每週天氣報告腳本 - for 水林, Yunlin

WEATHER=$(curl -s --max-time 15 "https://api.open-meteo.com/v1/forecast?latitude=23.71&longitude=120.21&daily=temperature_2m_max,temperature_2m_min,weathercode,precipitation_probability_max&timezone=Asia%2FTaipei&forecast_days=7")

if [ $? -eq 0 ]; then
  # Parse weather data (simplified)
  MAX_TEMP=$(echo "$WEATHER" | grep -oP '"temperature_2m_max":\[[\d.,]+\]' | head -1)
  MIN_TEMP=$(echo "$WEATHER" | grep -oP '"temperature_2m_min":\[[\d.,]+\]' | head -1)
  PRECIP=$(echo "$WEATHER" | grep -oP '"precipitation_probability_max":\[[\d.,]+\]' | head -1)
  
  echo "雲林水林天氣報告 $(date '+%Y/%m/%d')" > /tmp/weather-report.txt
  echo "==========" >> /tmp/weather-report.txt
  echo "$MAX_TEMP" >> /tmp/weather-report.txt
  echo "$MIN_TEMP" >> /tmp/weather-report.txt
  echo "$PRECIP" >> /tmp/weather-report.txt
else
  echo "Weather fetch failed" > /tmp/weather-report.txt
fi
