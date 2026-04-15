#!/usr/bin/env python3
"""fetch-stock-prices.py - 抓台股+美股最新股價，更新 JSON"""
import json, urllib.request, urllib.error, os
from datetime import datetime, timedelta

WORKSPACE = "/home/jhe/.openclaw/workspace"
TW_FILE = os.path.join(WORKSPACE, "taiwan_stock/taiwan_stocks.json")
TWSE_DATA_FILE = os.path.join(WORKSPACE, "taiwan_stock/twse_data.json")
TWSE_HTML_FILE = os.path.join(WORKSPACE, "taiwan_stock/twse_query.html")

def fetch_yahoo_price(symbol):
    url = "https://query1.finance.yahoo.com/v8/finance/chart/" + symbol + "?interval=1d&range=1d"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
            meta = data["chart"]["result"][0]["meta"]
            return meta.get("regularMarketPrice") or meta.get("previousClose")
    except Exception as e:
        print("  Warning: " + symbol + " failed: " + str(e))
        return None

def fetch_twse_realtime(codes):
    stock_str = "|".join("tse_" + c + ".tw" for c in codes)
    url = "http://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=" + stock_str + "&json=1&delay=0"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
        result = {}
        for item in data.get("msgArray", []):
            code = item.get("c", "")
            z = item.get("z", "-"); y = item.get("y", "-")
            o = item.get("o", "-"); h = item.get("h", "-"); l = item.get("l", "-")
            n = item.get("n", "")
            result[code] = {
                "name": n,
                "price": float(z) if z and z != "-" else None,
                "yclose": float(y) if y and y != "-" else None,
                "open": float(o) if o and o != "-" else None,
                "high": float(h) if h and h != "-" else None,
                "low": float(l) if l and l != "-" else None,
            }
        return result
    except Exception as e:
        print("  Warning: TWSE realtime failed: " + str(e))
        return {}

def fetch_twse_bwibbu():
    url = "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
        result = {}
        for item in data:
            code = item.get("Code", "")
            result[code] = {
                "pe": item.get("PEratio") or None,
                "dy": item.get("DividendYield") or None,
                "pb": item.get("PBratio") or None,
            }
        print("  BWIBBU fetched " + str(len(result)) + " stocks")
        return result
    except Exception as e:
        print("  Warning: BWIBBU failed: " + str(e))
        return {}

def fetch_twse_revenue():
    url = "https://openapi.twse.com.tw/v1/opendata/t187ap05_L"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
        result = {}
        for item in data:
            code = item.get("公司代號", "")
            result[code] = {
                "cur": float(item.get("營業收入-當月營收") or 0),
                "prev": float(item.get("營業收入-上月營收") or 0),
                "ly": float(item.get("營業收入-去年同月營收") or 0),
            }
        print("  Revenue fetched " + str(len(result)) + " stocks")
        return result
    except Exception as e:
        print("  Warning: Revenue failed: " + str(e))
        return {}

def fetch_twse_dividend():
    url = "https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
        print("  Dividend fetched " + str(len(data)) + " records")
        return data
    except Exception as e:
        print("  Warning: Dividend failed: " + str(e))
        return []

TW_STOCKS = [
    {"symbol": "0056.TW", "code": "0056", "annDiv": 1.6},
    {"symbol": "00692.TW", "code": "00692", "annDiv": 1.0},
    {"symbol": "00712.TW", "code": "00712", "annDiv": 0.35},
    {"symbol": "00713.TW", "code": "00713", "annDiv": 1.73},
    {"symbol": "00717.TW", "code": "00717", "annDiv": 0.6},
    {"symbol": "00878.TW", "code": "00878", "annDiv": 0.45},
    {"symbol": "00891.TW", "code": "00891", "annDiv": 0.3},
    {"symbol": "00940.TW", "code": "00940", "annDiv": 0.84},
    {"symbol": "009802.TW", "code": "009802", "annDiv": 0.5},
    {"symbol": "1101.TW", "code": "1101", "annDiv": None},
    {"symbol": "2886.TW", "code": "2886", "annDiv": None},
]
TW_CODES = [s["code"] for s in TW_STOCKS]

US_STOCKS = [
    {"symbol": "AAPL", "code": "AAPL"},
    {"symbol": "MSFT", "code": "MSFT"},
    {"symbol": "BND",  "code": "BND"},
]

# ─── 計算前一交易日 ─────────────────────────────
today = datetime.now()
prev = today - timedelta(days=1)
while prev.weekday() >= 5:
    prev -= timedelta(days=1)
prev_weekday = prev.strftime("%m/%d")

# ══════════════════════════════════════════════════
print("Fetching Taiwan stocks from Yahoo...")
tw_prices = {}
for item in TW_STOCKS:
    p = fetch_yahoo_price(item["symbol"])
    if p:
        tw_prices[item["code"]] = p
        print("  " + item["code"] + ": " + str(p))

print("Fetching US stocks from Yahoo...")
us_prices = {}
for item in US_STOCKS:
    p = fetch_yahoo_price(item["symbol"])
    if p:
        us_prices[item["code"]] = p
        print("  " + item["code"] + ": " + str(p))

print("Fetching TWSE realtime...")
tw_realtime = fetch_twse_realtime(TW_CODES)

print("Fetching TWSE BWIBBU...")
tw_bwibbu = fetch_twse_bwibbu()

print("Fetching TWSE revenue...")
tw_revenue = fetch_twse_revenue()

print("Fetching TWSE dividend...")
tw_dividend_raw = fetch_twse_dividend()
tw_dividend = [d for d in tw_dividend_raw if d.get("Code","") in TW_CODES]

# ─── 更新台股 JSON ───────────────────────────────
if tw_prices and os.path.exists(TW_FILE):
    tw_prev = {code: info["yclose"] for code, info in tw_realtime.items() if info.get("yclose")}
    print("  TWSE prev close: " + str(len(tw_prev)) + " stocks")
    with open(TW_FILE) as f:
        stocks = json.load(f)
    for s in stocks:
        code = s.get("symbol") or s.get("code")
        if code in tw_prices:
            s["price"] = tw_prices[code]
            if code in tw_prev:
                s["prev_price"] = tw_prev[code]
                s["prev_date"] = prev_weekday
            mv = s["shares"] * tw_prices[code]
            s["market_value"] = mv
            s["gain"] = mv - s.get("total_cost", 0)
            s["gain_pct"] = round(s["gain"] / s.get("total_cost", 1) * 100, 2)
    with open(TW_FILE, "w") as f:
        json.dump(stocks, f, ensure_ascii=False, indent=2)
    print("Updated TW JSON (" + str(len(tw_prices)) + " stocks)")

# ─── 儲存美股價格 ─────────────────────────────────
US_FILE = os.path.join(WORKSPACE, "us_stock/us_prices.json")
with open(US_FILE, "w") as f:
    json.dump({"prices": us_prices, "updated": datetime.now().strftime("%Y-%m-%d %H:%M")}, f)
print("Saved US prices (" + str(len(us_prices)) + " stocks)")

# ─── 生成 TWSE 靜態 HTML ────────────────────────
print("Generating TWSE static HTML...")

# ─── 準備 twse_data.json ─────────────────────────
tw_realtime_parsed = {}
for code in TW_CODES:
    info = tw_realtime.get(code, {})
    price = tw_prices.get(code)
    if not price:
        price = info.get("open") or info.get("price")
    yclose = info.get("yclose")
    change = round((price - yclose) / yclose * 100, 2) if price and yclose else 0.0
    ann_div = next((s["annDiv"] for s in TW_STOCKS if s["code"] == code), None)
    est_yield = round(ann_div / price * 100, 2) if ann_div and price else None
    bwibbu = tw_bwibbu.get(code, {})
    rev = tw_revenue.get(code, {})
    mom = round((rev.get("cur",0) - rev.get("prev",0)) / rev.get("prev",1) * 100, 1) if rev.get("prev") and rev.get("cur") else None
    tw_realtime_parsed[code] = {
        "price": price, "yclose": yclose, "change": change,
        "open": info.get("open"), "high": info.get("high"), "low": info.get("low"),
        "estYield": est_yield,
        "pe": bwibbu.get("pe"), "dy": bwibbu.get("dy"), "pb": bwibbu.get("pb"),
        "revCur": rev.get("cur"), "revPrev": rev.get("prev"), "revLy": rev.get("ly"), "revMom": mom,
    }

twse_data = {
    "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "prevDate": prev_weekday,
    "realtime": tw_realtime_parsed,
    "dividend": tw_dividend,
}
with open(TWSE_DATA_FILE, "w") as f:
    json.dump(twse_data, f, ensure_ascii=False, indent=2)

os.system("python3 " + WORKSPACE + "/scripts/gen-twse-html.py")

print("Generating stock overview...")
os.system("python3 " + WORKSPACE + "/scripts/gen-stock-html.py")
print("Done!")
