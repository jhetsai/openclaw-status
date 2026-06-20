#!/bin/bash
VERSION="2026.5.26"
GITCOMMIT="10ad3aa"

# Gateway uptime
GW_START_EPOCH=$(systemctl --user show openclaw-gateway --property ActiveEnterTimestamp --value 2>/dev/null)
if [ -n "$GW_START_EPOCH" ]; then
    GW_SECS=$(($(date +%s) - $(date -d "$GW_START_EPOCH" +%s 2>/dev/null || echo 0) ))
    GW_H=$((GW_SECS/3600))
    GW_M=$(( (GW_SECS%3600)/60 ))
    GW_STR="${GW_H}h ${GW_M}m"
else
    GW_STR="N/A"
fi

# System uptime
SYS_UPTIME=$(uptime -p 2>/dev/null | sed 's/up //' | sed 's/,.*//' | sed 's/ hour.*/h/' | sed 's/ minute.*/m/')
if [ -z "$SYS_UPTIME" ]; then
    SYS_UPTIME="N/A"
fi

# Model
MODEL="MiniMax-M2.7"

# CPU
LOAD=$(cat /proc/loadavg | awk '{print $1}')

# Memory
MEM_TOTAL=$(free -m | grep Mem | awk '{print $2}')
MEM_USED=$(free -m | grep Mem | awk '{print $3}')
MEM_PCT=$(free | grep Mem | awk '{printf "%.0f", $3*100/$2}')

# Disk
DISK_TOTAL=$(df -B1G / | tail -1 | awk '{print $2}' | sed 's/G//')
DISK_USED=$(df -B1G / | tail -1 | awk '{print $3}' | sed 's/G//')
DISK_PCT=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')

# OpenRouter - real API data
OR_KEY=$(cat ~/.openclaw/openclaw.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('env',{}).get('OPENROUTER_API_KEY',''))" 2>/dev/null)
OR_DATA=$(curl -s "https://openrouter.ai/api/v1/auth/key" -H "Authorization: Bearer $OR_KEY" 2>/dev/null)
OR_USAGE=$(echo "$OR_DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"{d['data']['usage']:.2f}\")" 2>/dev/null || echo "?")
OR_LIMIT=$(echo "$OR_DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['data']['limit'])" 2>/dev/null || echo "5")
OR_REMAINING=$(echo "$OR_DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"{d['data']['limit_remaining']:.2f}\")" 2>/dev/null || echo "?")

echo "🦞 OpenClaw $VERSION ($GITCOMMIT)"
echo "⏱️ Gateway: ${GW_STR}"
echo "⏱️ Uptime: gateway · system $SYS_UPTIME"
echo "🧠 Model: minimax/$MODEL"
echo "🖥️ CPU: $LOAD"
echo "💾 記憶體: ${MEM_USED}MB/${MEM_TOTAL}MB (${MEM_PCT}%)"
echo "💿 磁碟: ${DISK_USED}GB/${DISK_TOTAL}GB (${DISK_PCT}%)"
echo "📊 OpenRouter: \$$OR_USAGE / \$$OR_LIMIT (remaining: \$$OR_REMAINING)"
echo "🧵 Session: telegram:direct:1181571031"
echo "🚀 Gateway ✅"
