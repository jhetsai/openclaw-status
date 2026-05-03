#!/usr/bin/env python3
"""
持股技術分析報告
用法: python3 scripts/stock_ta_analysis.py [股票代碼]
      python3 scripts/stock_ta_analysis.py           # 分析所有持股
      python3 scripts/stock_ta_analysis.py 2886    # 分析特定股票
"""
import json, sys, os, math
from datetime import datetime

WORKSPACE = "/home/jhe/.openclaw/workspace"

# ====== Technical Indicator Functions ======

def calc_EMA(prices, period):
    k_val = 2 / (period + 1)
    ema = prices[0]
    result = [ema]
    for v in prices[1:]:
        ema = v * k_val + ema * (1 - k_val)
        result.append(ema)
    return result

def calc_KD(closes, period=9):
    K, D = 50, 50
    k_vals, d_vals = [], []
    for i in range(len(closes)):
        if i < period - 1:
            k_vals.append(None); d_vals.append(None)
            continue
        window = closes[i - period + 1:i + 1]
        low9 = min(c for c in window)
        high9 = max(c for c in window)
        c_close = closes[i]
        rsv = 50 if high9 == low9 else (c_close - low9) / (high9 - low9) * 100
        K = K * 2/3 + rsv * 1/3
        D = D * 2/3 + K * 1/3
        k_vals.append(round(K, 2)); d_vals.append(round(D, 2))
    return k_vals, d_vals

def calc_MACD(closes, fast=12, slow=26, signal=9):
    prices = list(closes)
    if len(prices) < slow:
        return [None]*len(prices), [None]*len(prices), [None]*len(prices)
    ema_fast = calc_EMA(prices, fast)
    ema_slow = calc_EMA(prices, slow)
    dif = [f - s for f, s in zip(ema_fast, ema_slow)]
    dem = calc_EMA(dif, signal)
    osc = [d - de for d, de in zip(dif, dem)]
    return dif, dem, osc

def calc_MA(prices, period):
    ma = []
    for i in range(len(prices)):
        if i < period - 1:
            ma.append(None)
        else:
            avg = sum(prices[i - period + 1:i + 1]) / period
            ma.append(round(avg, 2))
    return ma

def fmt(v, fmt='.2f'):
    return format(v, fmt) if v is not None else 'N/A'

# ====== Main Analysis ======

def analyze_stock(code, hist_tw, stock_info=None):
    """分析單一股票"""
    data = hist_tw.get(code, [])
    closes = [d["price"] for d in data]
    dates = [d["date"] for d in data]
    
    if len(closes) < 5:
        return None
    
    name = stock_info.get("name", code) if stock_info else code
    
    # Calculate indicators
    k_vals, d_vals = calc_KD(closes)
    dif, dem, osc = calc_MACD(closes)
    ma5 = calc_MA(closes, 5)
    ma10 = calc_MA(closes, 10)
    ma20 = calc_MA(closes, 20)
    ma60 = calc_MA(closes, 60) if len(closes) >= 60 else [None]*len(closes)
    
    # Latest values
    cur_price = closes[-1]
    cur_date = dates[-1]
    prev_price = closes[-2] if len(closes) >= 2 else cur_price
    change = cur_price - prev_price
    change_pct = change / prev_price * 100 if prev_price else 0
    
    k = k_vals[-1]
    d = d_vals[-1]
    dif_val = dif[-1]
    dem_val = dem[-1]
    osc_val = osc[-1]
    ma5_val = ma5[-1]
    ma10_val = ma10[-1]
    ma20_val = ma20[-1]
    ma60_val = ma60[-1]
    
    high20 = max(closes[-20:]) if len(closes) >= 20 else max(closes)
    low20 = min(closes[-20:]) if len(closes) >= 20 else min(closes)
    
    return {
        "code": code,
        "name": name,
        "date": cur_date,
        "price": cur_price,
        "change": change,
        "change_pct": change_pct,
        "k": k, "d": d,
        "dif": dif_val, "dem": dem_val, "osc": osc_val,
        "ma5": ma5_val, "ma10": ma10_val, "ma20": ma20_val, "ma60": ma60_val,
        "high20": high20, "low20": low20,
        "data_points": len(closes)
    }

def print_report(analysis):
    a = analysis
    code = a["code"]
    name = a["name"]
    print(f"\n{'='*50}")
    print(f"{code} {name} — 技術分析報告")
    print(f"{'='*50}")
    print(f"日期：{a['date']}  收盤：{a['price']} ({a['change']:+.2f} / {a['change_pct']:+.2f}%)")
    print(f"歷史資料：{a['data_points']} 筆")
    print()
    print(f"──  均線系統 ──────────────────────")
    print(f"  MA5:  {fmt(a['ma5'])}  {'▲' if a['price'] > a['ma5'] else '▼'}")
    print(f"  MA10: {fmt(a['ma10'])}  {'▲' if a['price'] > a['ma10'] else '▼'}")
    print(f"  MA20: {fmt(a['ma20'])}  {'▲' if a['price'] > a['ma20'] else '▼'}")
    print(f"  MA60: {fmt(a['ma60'])}")
    print()
    print(f"──  KD 指標 (9日) ────────────────")
    print(f"  K: {a['k']}  D: {a['d']}")
    print(f"  {'▶ 黃金交叉' if a['k'] > a['d'] else '▼ 死亡交叉'}")
    print()
    print(f"──  MACD (12/26/9) ───────────────")
    print(f"  DIF:  {fmt(a['dif'])}")
    print(f"  DEM:  {fmt(a['dem'])}")
    osc_ok = a['osc'] is not None
    print(f"  OSC:  {fmt(a['osc']) if osc_ok else 'N/A'}  ({'柱往上' if osc_ok and a['osc'] > 0 else '柱往下' if osc_ok else 'N/A'})")
    print()
    print(f"──  支撐/壓力 ───────────────────")
    print(f"  20日高：{a['high20']}  20日低：{a['low20']}")
    if a['ma20']:
        print(f"  短撐：{a['ma20']}  /  短壓：{a['ma5']}")
    print()
    print(f"──  綜合判斷 ─────────────────────")
    ma_ok = a['ma5'] and a['ma20'] and a['ma60']
    if ma_ok:
        bullish = a['price'] > a['ma5'] > a['ma20'] > a['ma60']
        trend = "📈 多頭排列" if bullish else "📉 空頭排列" if a['price'] < a['ma5'] < a['ma20'] < a['ma60'] else "🔄 整理格局"
    else:
        trend = "🔄 整理格局"
    kd_stat = "過熱" if a['k'] > 70 else "超賣" if a['k'] < 30 else "中性"
    macd_stat = "正向" if osc_ok and a['osc'] > 0 else "負向"
    print(f"  均線：{trend}")
    print(f"  KD：{kd_stat} (K={a['k']})")
    print(f"  MACD：{macd_stat}")
    print()

# ====== Entry Point ======

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Load history
    with open(f"{WORKSPACE}/stock_history.json") as f:
        hist = json.load(f)
    hist_tw = hist.get("tw", {})
    
    stock_names = {}
    tw_stocks_path = f"{WORKSPACE}/taiwan_stock/taiwan_stocks.json"
    if os.path.exists(tw_stocks_path):
        with open(tw_stocks_path) as f:
            tw_data = json.load(f)
            if isinstance(tw_data, list):
                for s in tw_data:
                    stock_names[s.get("symbol", s.get("code", "?"))] = s.get("name", s.get("symbol", "?"))
            elif isinstance(tw_data, dict):
                for code, s in tw_data.items():
                    stock_names[code] = s.get("name", code)
    
    # Determine targets
    if target:
        targets = [target]
    else:
        targets = list(hist_tw.keys())
    
    results = {}
    for code in targets:
        stock_data = hist_tw.get(code, [])
        if not stock_data:
            print(f"⚠️ {code} 無歷史資料")
            continue
        info = {"name": stock_names.get(code, code)}
        analysis = analyze_stock(code, hist_tw, info)
        if analysis:
            results[code] = analysis
    
    if not results:
        print("❌ 沒有可分析的股票")
        sys.exit(1)
    
    if target:
        # Single stock mode - detailed output
        print_report(results[target])
    else:
        # All stocks mode - summary table
        print(f"\n{'='*70}")
        print(f"持股技術分析總覽")
        print(f"{'='*70}")
        print(f"{'代碼':>6} {'名稱':<10} {'現價':>6} {'日%':>6} {'K':>5} {'D':>5} {'OSC':>6} {'MA5':>6} {'MA20':>6} {'MA60':>6} {'20H':>6} {'20L':>6} {'判斷'}")
        print(f"{'-'*70}")
        for code, a in sorted(results.items(), key=lambda x: x[0]):
            osc_ok = a['osc'] is not None
            osc_str = f"{a['osc']:+.2f}" if osc_ok else "N/A"
            ma5_str = f"{a['ma5']:.1f}" if a['ma5'] else "N/A"
            ma20_str = f"{a['ma20']:.1f}" if a['ma20'] else "N/A"
            ma60_str = f"{a['ma60']:.1f}" if a['ma60'] else "N/A"
            
            # Judgment
            kd = "過" if a['k'] > 70 else "賣" if a['k'] < 30 else "中"
            macd = "正" if osc_ok and a['osc'] > 0 else "負"
            if a['ma5'] and a['ma20'] and a['ma60']:
                if a['price'] > a['ma5'] > a['ma20'] > a['ma60']:
                    trend = "多"
                elif a['price'] < a['ma5'] < a['ma20'] < a['ma60']:
                    trend = "空"
                else:
                    trend = "整"
            else:
                trend = "?"
            
            print(f"{code:>6} {a['name']:<10} {a['price']:>6.1f} {a['change_pct']:>+5.1f}% {a['k']:>5.1f} {a['d']:>5.1f} {osc_str:>6} {ma5_str:>6} {ma20_str:>6} {ma60_str:>6} {a['high20']:>6.1f} {a['low20']:>6.1f} {kd}{macd}{trend}")
        
        print(f"{'-'*70}")
        print(f"\n說明： KD狀態(過/賣/中) | MACD(正/負) | 均線判斷(多/空/整/?)")
        print(f"      日% = 單日價格變動%")
