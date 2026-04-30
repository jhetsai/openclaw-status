import json
from datetime import datetime

# 讀取 us_prices.json (有最新報價)
with open('/home/jhe/.openclaw/workspace/us_stock/us_prices.json') as f:
    prices_data = json.load(f)
prices = prices_data.get('prices', {})

# 讀取 us_stocks.json (有持股明細)
with open('/home/jhe/.openclaw/workspace/us_stock/us_stocks.json') as f:
    stocks = json.load(f)

# 更新價格
for s in stocks:
    sym = s.get('symbol', '')
    if sym in prices:
        s['price'] = prices[sym]

# 加入 update_time
now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
for s in stocks:
    s['update_time'] = now

# 存回
with open('/home/jhe/.openclaw/workspace/us_stock/us_stocks.json', 'w') as f:
    json.dump(stocks, f, ensure_ascii=False, indent=2)

print(f'Updated {len(stocks)} stocks with latest prices')
for s in stocks:
    print(f"  {s['symbol']}: {s['price']} (cost {s.get('cost','?')})")