#!/usr/bin/env python3
"""
gen_esp32_portfolio.py
從 portfolio_data.json 直接取 summary，再從 stocks 陣列 aggregate tw/us 子項，不做計算。
"""
import json, os
from datetime import datetime

WORKSPACE = os.environ.get('WORKSPACE', '/home/jhe/.openclaw/workspace')
IN_FILE  = os.path.join(WORKSPACE, 'assets', 'portfolio_data.json')
OUT_FILE = os.path.join(WORKSPACE, 'assets', 'esp32_portfolio.json')

with open(IN_FILE) as f:
    pf = json.load(f)

now_str = datetime.now().strftime('%Y-%m-%d %H:%M')

summary  = pf.get('summary', {})
stocks   = pf.get('stocks', {})
tw_list  = stocks.get('tw', [])
us_list  = stocks.get('us', [])
fx       = pf.get('fx', {})
usd_cash = pf.get('usd_cash', {})
jpy_cash = pf.get('jpy_cash', {})

# ── 從 stocks 陣列 aggregate tw/us 子項（不做計算，只加總）─────────────
tw_cost = sum(s.get('total_cost', 0) for s in tw_list)
tw_mkt  = sum(s.get('market_value', 0) for s in tw_list)

us_cost_twd = sum(s.get('costTwd', 0) for s in us_list)
us_mkt_twd  = sum(s.get('mktvalTwd', 0) for s in us_list)

# 取得 USD_TWD 匯率（movers US stock TWD 換算用）
usd_twd_rate = fx.get('USD_TWD', 31.5)

# ── 計算每檔持倉的「今日脈跌」與「脈跌金額」─────────────
def _calc_chg(stock, market):
    """回傳 (chg_pct, chg_amount_twd)"""
    p = stock.get('price', 0) or 0
    prev = stock.get('prev_price', 0) or 0
    sh = stock.get('shares', 0) or 0
    if not p or not prev:
        return (0.0, 0.0)
    chg_pct = (p - prev) / prev * 100
    if market == 'tw':
        chg_amount = (p - prev) * sh   # TWD
    else:  # us
        chg_amount = (p - prev) * sh * usd_twd_rate  # 轉 TWD
    return (chg_pct, chg_amount)

all_movers = []
for s in tw_list:
    pct, amt = _calc_chg(s, 'tw')
    all_movers.append({
        'symbol': s.get('symbol', ''),
        'name':   s.get('name', ''),
        'market': 'tw',
        'chg_pct':  round(pct, 2),
        'chg_amount': round(amt, 0),
        'mktval': s.get('market_value', 0),
    })
for s in us_list:
    pct, amt = _calc_chg(s, 'us')
    all_movers.append({
        'symbol': s.get('symbol', ''),
        'name':   s.get('name', ''),
        'market': 'us',
        'chg_pct':  round(pct, 2),
        'chg_amount': round(amt, 0),
        'mktval': s.get('mktvalTwd', 0),
    })

# 按市值排序，取前 5
top_movers = sorted(all_movers, key=lambda x: x['mktval'], reverse=True)[:5]
# 按漲幅排序，取前 5
top_gainers = sorted(all_movers, key=lambda x: x['chg_pct'], reverse=True)[:5]

# ── 今日脈跌：台股 (price - prev_price) * shares，美股換算 TWD 後加總 ───────
def _today_change_tw(stocks):
    total = 0.0
    for s in stocks:
        p = s.get('price', 0) or 0
        prev = s.get('prev_price', 0) or 0
        sh = s.get('shares', 0) or 0
        if p and prev:
            total += (p - prev) * sh
    return total

def _today_change_us(stocks, usd_twd):
    total = 0.0
    for s in stocks:
        p = s.get('price', 0) or 0
        prev = s.get('prev_price', 0) or 0
        sh = s.get('shares', 0) or 0
        if p and prev:
            total += (p - prev) * sh  # USD
    return total * usd_twd  # 換 TWD

usd_twd_rate = fx.get('USD_TWD', 31.5)
tw_day = _today_change_tw(tw_list)
us_day = _today_change_us(us_list, usd_twd_rate)
total_day_twd = round(tw_day + us_day)
total_mkt = summary.get('stockMktval', 0)
total_day_pct = round(total_day_twd / total_mkt * 100, 2) if total_mkt else 0.0

# ── 讀取太陽能累積發電量 ────────────────────────────────────────────────
solar_kwh = 0.0
solar_csv = os.path.join(WORKSPACE, 'solar_history.csv')
if os.path.exists(solar_csv):
    with open(solar_csv) as f:
        lines = f.read().strip().split('\n')
    if lines:
        last = lines[-1].split(',')
        if len(last) >= 2:
            try:
                solar_kwh = float(last[1])
            except ValueError:
                pass

# ── 組建 esp32_portfolio.json ─────────────────────────────────────────
out = {
    "updated": now_str,
    "summary": {
        "total_cost":     summary.get('stockCost', 0),
        "total_mktval":   summary.get('stockMktval', 0),
        "total_gain":     summary.get('stockMktval', 0) - summary.get('stockCost', 0),
        "total_gain_pct": round(
            (summary.get('stockMktval', 0) - summary.get('stockCost', 0)) / summary.get('stockCost', 1) * 100, 2
        ) if summary.get('stockCost', 0) else 0,
        "today_change":   total_day_twd,
        "today_change_pct": total_day_pct,
        "annual_div":     summary.get('annualDiv', 0),
        "yield_cost":     summary.get('yieldCost', '0%'),
        "yield_cur":      summary.get('yieldCur', '0%')
    },
    "tw": {
        "cost":    round(tw_cost),
        "mktval":  round(tw_mkt),
        "gain":     round(tw_mkt - tw_cost),
        "gain_pct": round((tw_mkt - tw_cost) / tw_cost * 100, 2) if tw_cost else 0
    },
    "us": {
        "cost_twd":  round(us_cost_twd),
        "mktval_twd": round(us_mkt_twd),
        "gain_twd":   round(us_mkt_twd - us_cost_twd),
        "gain_pct":   round((us_mkt_twd - us_cost_twd) / us_cost_twd * 100, 2) if us_cost_twd else 0
    },
    "cash": {
        "usd": {
            "amount":       usd_cash.get('cash_usd', 0),
            "in_twd":       round(usd_cash.get('cash_usd', 0) * fx.get('USD_TWD', 31.5)),
            "rate_usd_twd": fx.get('USD_TWD', 31.5)
        },
        "jpy": {
            "amount":       jpy_cash.get('cash_jpy', 0),
            "in_twd":       round(jpy_cash.get('cash_jpy', 0) * fx.get('JPY_TWD', 0.19)),
            "rate_jpy_twd": fx.get('JPY_TWD', 0.19)
        }
    },
    "fx": {
        "usd_twd": fx.get('USD_TWD', 31.5),
        "jpy_twd": fx.get('JPY_TWD', 0.19),
        "updated": fx.get('updated', now_str)
    },
    "movers": {
        "top": top_movers,
        "gainers": top_gainers,
        "total": len(all_movers)
    },
    "solar_kwh": round(solar_kwh, 1)
}

os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
with open(OUT_FILE, 'w') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print(f"  esp32_portfolio.json saved ({OUT_FILE})")
print(f"  total_cost={out['summary']['total_cost']:,}  total_mktval={out['summary']['total_mktval']:,}")
print(f"  tw: cost={out['tw']['cost']:,}  mktval={out['tw']['mktval']:,}  gain_pct={out['tw']['gain_pct']}%")
print(f"  us: cost={out['us']['cost_twd']:,}  mktval={out['us']['mktval_twd']:,}  gain_pct={out['us']['gain_pct']}%")

# 上傳 R2
try:
    import boto3
    keys_file = os.path.expanduser('~/.api_keys')
    keys = {}
    if os.path.exists(keys_file):
        with open(keys_file) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    keys[k.strip()] = v.strip()

    s3 = boto3.client('s3',
        endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
        aws_access_key_id=keys.get('R2_ACCESS_KEY'),
        aws_secret_access_key=keys.get('R2_SECRET_KEY'))
    s3.upload_file(OUT_FILE, 'shared-files', 'assets/esp32_portfolio.json',
                   ExtraArgs={'ContentType': 'application/json'})
    print("  Uploaded to R2: assets/esp32_portfolio.json")
except Exception as e:
    print(f"  R2 upload failed: {e}")
