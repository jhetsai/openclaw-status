#!/usr/bin/env python3
"""fetch-stock-prices.py - 抓台股+美股最新股價，更新 JSON"""
import json, urllib.request, urllib.error, re, os
from datetime import datetime

WORKSPACE = "/home/jhe/.openclaw/workspace"
TW_FILE = os.path.join(WORKSPACE, "taiwan_stock/taiwan_stocks.json")

# ─── Yahoo Finance 抓價 ───────────────────────────
def fetch_yahoo_price(symbol):
    """從 Yahoo Finance 抓單一股票最新價格"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json'
        })
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
            meta = data['chart']['result'][0]['meta']
            return meta.get('regularMarketPrice') or meta.get('previousClose')
    except Exception as e:
        print(f"  ⚠️ {symbol} 抓價失敗: {e}")
        return None

def fetch_yahoo_prev_close(symbol):
    """從 Yahoo Finance 抓前日收盤價"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json'
        })
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
            closes = [c for c in data['chart']['result'][0]['indicators']['quote'][0]['close'] if c]
            return closes[-2] if len(closes) >= 2 else closes[-1]
    except:
        return None

# ─── 台股持股清單 ─────────────────────────────────
TW_STOCKS = [
    {"symbol": "0056.TW", "code": "0056"},
    {"symbol": "00692.TW", "code": "00692"},
    {"symbol": "00712.TW", "code": "00712"},
    {"symbol": "00713.TW", "code": "00713"},
    {"symbol": "00717.TW", "code": "00717"},
    {"symbol": "00878.TW", "code": "00878"},
    {"symbol": "00891.TW", "code": "00891"},
    {"symbol": "00940.TW", "code": "00940"},
    {"symbol": "009802.TW", "code": "009802"},
    {"symbol": "1101.TW", "code": "1101"},
    {"symbol": "2886.TW", "code": "2886"},
]

# ─── 美股持股清單 ─────────────────────────────────
US_STOCKS = [
    {"symbol": "AAPL", "code": "AAPL"},
    {"symbol": "MSFT", "code": "MSFT"},
    {"symbol": "BND",  "code": "BND"},
]

print("📈 抓取台股價格...")
tw_prices = {}

for item in TW_STOCKS:
    sym = item["symbol"]
    p = fetch_yahoo_price(sym)
    if p:
        tw_prices[item["code"]] = p
        print(f"  {item['code']}: {p}")

# ─── 美股價格 ──────────────────────────────────────
print("💵 抓取美股價格...")
us_prices = {}
for item in US_STOCKS:
    sym = item["symbol"]
    p = fetch_yahoo_price(sym)
    if p:
        us_prices[item["code"]] = p
        print(f"  {item['code']}: {p}")

# ─── 更新台股 JSON ───────────────────────────────
if tw_prices and os.path.exists(TW_FILE):
    with open(TW_FILE) as f:
        stocks = json.load(f)
    for s in stocks:
        code = s.get("symbol") or s.get("code")
        if code in tw_prices:
            s["prev_price"] = fetch_yahoo_prev_close(code + ".TW") or s.get("price")
            s["price"] = tw_prices[code]
            mv = s["shares"] * tw_prices[code]
            s["market_value"] = mv
            s["gain"] = mv - s.get("total_cost", 0)
            s["gain_pct"] = round(s["gain"] / s.get("total_cost", 1) * 100, 2)
    with open(TW_FILE, "w") as f:
        json.dump(stocks, f, ensure_ascii=False, indent=2)
    print(f"✅ 台股 JSON 更新完成（{len(tw_prices)} 檔）")

# ─── 儲存美股價格到暫存 ──────────────────────────
US_FILE = os.path.join(WORKSPACE, "us_stock/us_prices.json")
with open(US_FILE, "w") as f:
    json.dump({"prices": us_prices, "updated": datetime.now().strftime("%Y-%m-%d %H:%M")}, f)
print(f"✅ 美股價格暫存完成（{len(us_prices)} 檔）")

print("📊 生成持股總攬...")
os.system(f"python3 {WORKSPACE}/scripts/gen-stock-html.py")
