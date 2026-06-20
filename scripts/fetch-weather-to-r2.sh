#!/bin/bash
# 2026-06-06 重構：選項 B - CWA 為主
# 1. CWA 上傳 R2（主預報，給儀表板 + 聊天用）
# 2. WeatherAPI + Open-Meteo + Windy 上傳 R2（cross-check / fallback）
set -a
source ~/.api_keys
set +a
python3 /home/jhe/.openclaw/workspace/scripts/cwa_weather_to_r2.py

echo "=== [$(date '+%H:%M:%S')] weather refresh start ==="
python3 /home/jhe/.openclaw/workspace/scripts/cwa_weather_to_r2.py
echo "---"
python3 /home/jhe/.openclaw/workspace/scripts/fetch-weather-to-r2.py
echo "=== [$(date '+%H:%M:%S')] weather refresh done ==="
