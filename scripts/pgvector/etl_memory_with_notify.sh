#!/bin/bash
# 向量資料庫同步 + 完成通知

cd /home/jhe/.openclaw/workspace/scripts/pgvector

# 執行 ETL
START_TIME=$(date +%s)
python3 etl_memory_v2.py >> logs/etl_memory.log 2>&1
RESULT=$?
END_TIME=$(date +%s)

# 計算耗時
DURATION=$((END_TIME - START_TIME))
MINS=$((DURATION / 60))
SECS=$((DURATION % 60))

# 解析 log 取得統計
LOG_FILE="logs/etl_memory.log"
FILES=$(grep "Files processed:" "$LOG_FILE" | tail -1 | grep -o '[0-9]\+' | head -1)
CHUNKS=$(grep "Total chunks:" "$LOG_FILE" | tail -1 | grep -o '[0-9]\+')

if [ -z "$FILES" ]; then FILES="?"; fi
if [ -z "$CHUNKS" ]; then CHUNKS="?"; fi

if [ $RESULT -eq 0 ]; then
  python3 -c "
import urllib.request
import json

token = '8793435853:AAHF2snG1sYEpno-O0uvvRyPL52cqdxER8A'
chat_id = '1181571031'

text = '''✅ 向量資料庫同步完成

| 項目 | 數值 |
|------|------|
| 執行時間 | ''' + str($MINS) + ''' 分 ''' + str($SECS) + ''' 秒 |
| 檔案數量 | ''' + str($FILES) + ''' 個 |
| Chunk 總數 | ''' + str($CHUNKS) + ''' |

下次執行：6/1（二）16:00'''

url = f'https://api.telegram.org/bot{token}/sendMessage'
data = json.dumps({'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}).encode()
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
urllib.request.urlopen(req)
"
else
  python3 -c "
import urllib.request
import json

token = '8793435853:AAHF2snG1sYEpno-O0uvvRyPL52cqdxER8A'
chat_id = '1181571031'
text = '❌ 向量資料庫同步失敗'

url = f'https://api.telegram.org/bot{token}/sendMessage'
data = json.dumps({'chat_id': chat_id, 'text': text}).encode()
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
urllib.request.urlopen(req)
"
fi