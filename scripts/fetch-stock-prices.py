#!/usr/bin/env python3
"""fetch-stock-prices.py - 抓台股+美股最新股價，更新 JSON"""
import json, urllib.request, urllib.error, os, subprocess
from datetime import datetime, timedelta

WORKSPACE = "/home/jhe/.openclaw/workspace"

KEYS = {}
key_file = os.path.expanduser("~/.api_keys")
if os.path.exists(key_file):
    with open(key_file) as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                KEYS[k] = v
FINNHUB_KEY = KEYS.get("FINNHUB_KEY", "")
TW_FILE = os.path.join(WORKSPACE, "taiwan_stock/taiwan_stocks.json")
TWSE_DATA_FILE = os.path.join(WORKSPACE, "taiwan_stock/twse_data.json")
TWSE_HTML_FILE = os.path.join(WORKSPACE, "taiwan_stock/twse_query.html")

YAHOO_HOSTS = ['query1.finance.yahoo.com', 'query2.finance.yahoo.com']

def fetch_yahoo_tw_price(code):
    """Fetch real-time Taiwan stock price from tw.stock.yahoo.com"""
    url = f"https://tw.stock.yahoo.com/quote/{code}"
    try:
        result = subprocess.run(
            ['curl', '-s', '--max-time', '10', '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36', url],
            capture_output=True, text=True, timeout=12
        )
        if result.returncode == 0 and result.stdout.strip():
            import re
            html = result.stdout
            # Try to find real-time price from the page's JSON data
            m = re.search(r'"price"\s*:\s*\{\s*"raw"\s*:\s*([0-9.]+)', html)
            if m:
                return float(m.group(1))
            # Fallback: try to find price in different format
            m = re.search(r'"regularMarketPrice"\s*:\s*([0-9.]+)', html)
            if m:
                return float(m.group(1))
        return None
    except Exception as e:
        print(f"  Warning: Yahoo TW {code} error: {e}")
        return None

def fetch_yahoo_price(symbol):
    for host in YAHOO_HOSTS:
        url = f"https://{host}/v8/finance/chart/{symbol}?interval=1d&range=1d"
        try:
            result = subprocess.run(
                ['curl', '-4', '-s', '--max-time', '8', '-H', 'User-Agent: Mozilla/5.0', url],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                result_data = data.get("chart", {}).get("result")
                if result_data:
                    meta = result_data[0]["meta"]
                    return meta.get("regularMarketPrice") or meta.get("previousClose")
            else:
                print(f"  Warning: {symbol} @ {host} failed (rc={result.returncode}), trying next...")
                continue
        except Exception as e:
            print(f"  Warning: {symbol} @ {host} error: {e}, trying next...")
            continue
    print("  Warning: " + symbol + " all Yahoo hosts failed")
    return None

def fetch_yahoo_quote(symbol):
    """Fetch price and prev from Yahoo, returns (price, prev)"""
    for host in YAHOO_HOSTS:
        url = f"https://{host}/v8/finance/chart/{symbol}?interval=1d&range=5d"
        try:
            result = subprocess.run(
                ['curl', '-4', '-s', '--max-time', '8', '-H', 'User-Agent: Mozilla/5.0', url],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                result_data = data.get("chart", {}).get("result")
                if result_data:
                    meta = result_data[0]["meta"]
                    price = meta.get("regularMarketPrice") or meta.get("previousClose")
                    prev = meta.get("previousClose") or meta.get("chartPreviousClose")
                    if not prev:
                        closes = result_data[0].get("indicators", {}).get("quote", [{}])[0].get("close", [])
                        if len(closes) >= 2:
                            prev = closes[-2]
                    return price, prev
            else:
                continue
        except Exception:
            continue
    return None, None

def fetch_taiwan_futures(symbol):
    """Fetch Taiwan futures (WTX&, WTXP&) from Yahoo Taiwan page"""
    url = f"https://tw.stock.yahoo.com/future/{symbol}"
    try:
        result = subprocess.run(
            ['curl', '-s', '--max-time', '10', '-H', 'User-Agent: Mozilla/5.0', url],
            capture_output=True, text=True, timeout=12
        )
        if result.returncode == 0 and result.stdout.strip():
            import re
            html = result.stdout
            m = re.search(r'"price"\s*:\s*\{\s*"raw"\s*:\s*"?([0-9.]+)', html)
            if m:
                return float(m.group(1))
        return None
    except Exception as e:
        print(f"  Warning: {symbol} error: {e}")
        return None

def fetch_twse_realtime(codes):
    stock_str = "|".join("tse_" + c + ".tw" for c in codes)
    url = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=" + stock_str + "&json=1&delay=0"
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
            # Use o (open/auction price) only if z is not available; prefer Yahoo fallback over unreliable auction price
            price_raw = z if z and z != "-" else None
            result[code] = {
                "name": n,
                "price": float(price_raw) if price_raw else None,
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
    # US Stocks (Finnhub)
    {"symbol": "AAPL", "code": "AAPL"},
    {"symbol": "MSFT", "code": "MSFT"},
    {"symbol": "BND",  "code": "BND"},
    # Other indices (Yahoo only)
    {"symbol": "^FNMR", "code": "FNMR", "ref_only": True},
    # Taiwan futures (Yahoo only)
    {"symbol": "WTX&", "code": "WTX", "ref_only": True},
    {"symbol": "WTXP&", "code": "WTXP", "ref_only": True},
    # US Indices via Finnhub ETF equivalents
    {"symbol": "SPY", "code": "SP500", "ref_only": True},    # S&P 500 ETF
    {"symbol": "QQQ", "code": "NAS100", "ref_only": True},   # NASDAQ 100 ETF
    {"symbol": "DIA", "code": "DOW", "ref_only": True},     # DOW ETF
    {"symbol": "VIXY", "code": "VIX", "ref_only": True},    # VIX ETF
    {"symbol": "TLT", "code": "TNX", "ref_only": True},      # 20Y Bond ETF
    {"symbol": "GLD", "code": "GOLD", "ref_only": True},    # Gold ETF
    {"symbol": "USO", "code": "OIL", "ref_only": True},     # Oil ETF
    # Taiwan (Yahoo only)
    {"symbol": "^TWII", "code": "TAIEX", "ref_only": True},
]

# ─── 計算前一交易日 ─────────────────────────────
today = datetime.now()
prev = today - timedelta(days=1)
while prev.weekday() >= 5:
    prev -= timedelta(days=1)
prev_weekday = prev.strftime("%m/%d")

# ══════════════════════════════════════════════════
print("Fetching Taiwan stocks from TWSE API...")
tw_prices = {}; tw_realtime = {}
tw_realtime = fetch_twse_realtime(TW_CODES)
for code, info in tw_realtime.items():
    if info.get("price"):
        tw_prices[code] = info["price"]
        print("  " + code + ": " + str(info["price"]))

# Always supplement missing stocks with Yahoo TW real-time
missing = [c for c in TW_CODES if c not in tw_prices]
if missing:
    print(f"  TWSE got {len(tw_prices)} stocks, supplementing {len(missing)} missing with Yahoo TW real-time...")
    tw_yahoo_tw_ok = 0
    for code in missing:
        price = fetch_yahoo_tw_price(code)
        if price:
            tw_prices[code] = price
            print("  [Yahoo TW] " + code + ": " + str(price))
            tw_yahoo_tw_ok += 1
    print("  Yahoo TW supplemented " + str(tw_yahoo_tw_ok) + " stocks")

# Final fallback: if Yahoo TW still missing some, use Yahoo Finance API (delayed)
missing2 = [c for c in TW_CODES if c not in tw_prices]
if missing2:
    print("  Still missing " + str(len(missing2)) + " stocks, using Yahoo Finance API (delayed)...")
    for code in missing2:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}.TW?interval=1d&range=1d"
        try:
            result = subprocess.run(
                ['curl', '-4', '-s', '--max-time', '8', '-H', 'User-Agent: Mozilla/5.0', url],
                capture_output=True, text=True, timeout=12
            )
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                meta = data['chart']['result'][0]['meta']
                price = meta.get('regularMarketPrice') or meta.get('previousClose')
                if price:
                    tw_prices[code] = price
                    print("  [Yahoo API] " + code + ": " + str(price))
                else:
                    print("  [Yahoo API] " + code + ": no price data")
            else:
                print("  [Yahoo API] " + code + ": failed (rc=" + str(result.returncode) + ")")
        except Exception as e:
            print("  [Yahoo API] " + code + ": error " + str(e))
    print("  After fallback: " + str(len(tw_prices)) + " stocks total")

def fetch_finnhub_quote(symbol):
    """Fetch US stock price+prev from Finnhub, returns (price, prev) or (None, None)"""
    if not FINNHUB_KEY:
        return None, None
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_KEY}"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("c") and data["c"] > 0:
                return data["c"], data.get("pc", data["c"])
    except Exception:
        pass
    return None, None

print("Fetching US stocks from Finnhub...")
us_prices = {}
us_prev = {}
for item in US_STOCKS:
    sym = item["symbol"]
    code = item["code"]
    # WTX& and WTXP& need special handling via Taiwan page
    if sym in ("WTX&", "WTXP&"):
        p = fetch_taiwan_futures(sym)
        if p:
            us_prices[code] = p
            print(f"  {code}: {p} (Taiwan futures)")
        else:
            print(f"  {code}: failed")
    else:
        # Try Finnhub first (it provides prev_close directly)
        price, prev = fetch_finnhub_quote(sym)
        if price:
            us_prices[code] = price
            us_prev[code] = prev
            src = "Finnhub"
        else:
            # Yahoo fallback
            price, prev = fetch_yahoo_quote(sym)
            if price:
                us_prices[code] = price
                if prev:
                    us_prev[code] = prev
                src = "Yahoo"
            else:
                print(f"  {code}: failed (both Finnhub and Yahoo)")
                continue
        print(f"  {code}: {us_prices[code]} ({src})")

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
            s["total_cost"] = s["shares"] * s["cost"]
            s["gain"] = s["market_value"] - s["total_cost"]
            s["gain_pct"] = round(s["gain"] / s.get("total_cost", 1) * 100, 2)
            s["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(TW_FILE, "w") as f:
        json.dump(stocks, f, ensure_ascii=False, indent=2)
    print("Updated TW JSON (" + str(len(tw_prices)) + " stocks)")

# ─── 儲存美股價格 ─────────────────────────────────
US_FILE = os.path.join(WORKSPACE, "us_stock/us_prices.json")
us_save = {"prices": us_prices, "prev": us_prev, "updated": datetime.now().strftime("%Y-%m-%d %H:%M")}
with open(US_FILE, "w") as f:
    json.dump(us_save, f)
print("Saved US prices (" + str(len(us_prices)) + " stocks), prev: " + str(len(us_prev)))

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
    "upcoming_div": [
        d for d in tw_dividend
        if d.get("Date","") >= (lambda t: f"{t.year-1911:03d}{t.month:02d}{t.day:02d}")(datetime.now())
    ]
}
with open(TWSE_DATA_FILE, "w") as f:
    json.dump(twse_data, f, ensure_ascii=False, indent=2)

os.system("python3 " + WORKSPACE + "/scripts/gen-twse-html.py")

print("Generating stock overview...")
os.system("python3 " + WORKSPACE + "/scripts/gen-stock-html.py")
print("Done!")
