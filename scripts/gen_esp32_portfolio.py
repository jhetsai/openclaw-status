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
        ) if summary.get('stockCost', 0) else 0
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
