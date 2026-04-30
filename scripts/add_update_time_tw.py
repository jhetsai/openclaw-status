import json, sys
from datetime import datetime

WORKSPACE = '/home/jhe/.openclaw/workspace'
NOW = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

with open(f'{WORKSPACE}/taiwan_stock/taiwan_stocks.json') as f:
    data = json.load(f)
for s in data:
    s['update_time'] = NOW
with open(f'{WORKSPACE}/taiwan_stock/taiwan_stocks.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f'Taiwan stocks updated with time: {NOW}')