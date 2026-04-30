import json
NOW = '2026-04-22 09:40:12'
with open('/home/jhe/.openclaw/workspace/us_stock/us_stocks.json') as f:
    data = json.load(f)
for s in data:
    s['update_time'] = NOW
with open('/home/jhe/.openclaw/workspace/us_stock/us_stocks.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print('Done')