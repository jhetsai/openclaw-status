#!/usr/bin/env python3
"""產生技術分析儀表板 PDF（HTML 版）"""
import json, sys, os, math
from datetime import datetime

WORKSPACE = "/home/jhe/.openclaw/workspace"

# ====== Technical Indicators ======

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

def fmt(v):
    return f"{v:.2f}" if v is not None else "N/A"

def analyze(code):
    with open(f"{WORKSPACE}/stock_history.json") as f:
        hist = json.load(f)
    tw = hist.get("tw", {})
    data = tw.get(code, [])
    closes = [d["price"] for d in data]
    dates = [d["date"] for d in data]
    
    # Lookup stock name from taiwan_stocks.json
    stock_name = code
    tw_stocks_path = f"{WORKSPACE}/taiwan_stock/taiwan_stocks.json"
    if os.path.exists(tw_stocks_path):
        with open(tw_stocks_path) as f:
            tw_data = json.load(f)
            if isinstance(tw_data, list):
                for s in tw_data:
                    sym = s.get("symbol", s.get("code", "?"))
                    if sym == code:
                        stock_name = s.get("name", code)
                        break
    
    k_vals, d_vals = calc_KD(closes)
    dif, dem, osc = calc_MACD(closes)
    ma5 = calc_MA(closes, 5)
    ma10 = calc_MA(closes, 10)
    ma20 = calc_MA(closes, 20)
    ma60 = calc_MA(closes, 60)
    
    cur = closes[-1]
    prev = closes[-2]
    chg = cur - prev
    chg_pct = chg / prev * 100
    
    k = k_vals[-1]
    d = d_vals[-1]
    dif_v = dif[-1]
    dem_v = dem[-1]
    osc_v = osc[-1]
    ma5_v = ma5[-1]
    ma10_v = ma10[-1]
    ma20_v = ma20[-1]
    ma60_v = ma60[-1]
    
    high20 = max(closes[-20:])
    low20 = min(closes[-20:])
    high60 = max(closes[-60:]) if len(closes) >= 60 else max(closes)
    low60 = min(closes[-60:]) if len(closes) >= 60 else min(closes)
    
    # Trend judgment
    if ma5_v and ma20_v and ma60_v:
        if cur > ma5_v > ma20_v > ma60_v:
            ma_trend = "多頭排列 📈"
        elif cur < ma5_v < ma20_v < ma60_v:
            ma_trend = "空頭排列 📉"
        else:
            ma_trend = "整理格局 🔄"
    else:
        ma_trend = "整理格局 🔄"
    
    kd_signal = "黃金交叉 ▶ (K>D)" if k > d else "死亡交叉 ▼ (K<D)"
    kd_status = "過熱 (>70)" if k > 70 else "超賣 (<30)" if k < 30 else "中性"
    
    osc_dir = "往上" if osc_v and osc_v > 0 else "往下"
    macd_trend = "正向柱" if osc_v and osc_v > 0 else "負向柱"
    
    # Support/Resistance
    r1 = ma20_v
    r2 = ma5_v
    s1 = ma10_v
    s2 = low20
    
    # 過去幾天趨勢描述
    recent_5 = closes[-5:]
    trend_desc = "持平" if abs(recent_5[-1] - recent_5[0]) / recent_5[0] < 0.02 else "上漲" if recent_5[-1] > recent_5[0] else "下跌"
    
    return {
        "code": code,
        "name": stock_name,
        "date": dates[-1],
        "price": cur,
        "chg": chg,
        "chg_pct": chg_pct,
        "k": k, "d": d,
        "dif": dif_v, "dem": dem_v, "osc": osc_v,
        "ma5": ma5_v, "ma10": ma10_v, "ma20": ma20_v, "ma60": ma60_v,
        "high20": high20, "low20": low20,
        "high60": high60, "low60": low60,
        "ma_trend": ma_trend,
        "kd_signal": kd_signal,
        "kd_status": kd_status,
        "osc_dir": osc_dir,
        "macd_trend": macd_trend,
        "r1": r1, "r2": r2, "s1": s1, "s2": s2,
        "data_points": len(closes)
    }

def build_html(a):
    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<title>{a['code']} 技術分析儀表板</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, "Microsoft JhengHei", sans-serif; background: #0a0a1a; color: white; padding: 20px; }}
  .container {{ max-width: 900px; margin: 0 auto; }}
  
  .header {{ background: linear-gradient(135deg, #1a1a2e, #16213e); border-radius: 16px; padding: 24px; margin-bottom: 16px; }}
  .header h1 {{ font-size: 1.8em; margin-bottom: 4px; }}
  .header .subtitle {{ color: #888; font-size: 0.85em; }}
  .price-block {{ display: flex; align-items: baseline; gap: 16px; margin-top: 12px; }}
  .price {{ font-size: 2.4em; font-weight: bold; }}
  .chg {{ font-size: 1.2em; padding: 4px 12px; border-radius: 8px; }}
  .chg.up {{ background: #d32f2f; color: white; }}
  .chg.down {{ background: #1976d2; color: white; }}
  .chg.flat {{ background: #555; color: #ccc; }}
  
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }}
  .card {{ background: #12122a; border-radius: 12px; padding: 16px; }}
  .card h3 {{ color: #aaa; font-size: 0.8em; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; border-bottom: 1px solid #333; padding-bottom: 6px; }}
  .card h3.green {{ color: #4caf50; }}
  .card h3.red {{ color: #ef5350; }}
  .card h3.blue {{ color: #42a5f5; }}
  .card h3.purple {{ color: #ab47bc; }}
  
  .row {{ display: flex; justify-content: space-between; padding: 4px 0; font-size: 0.9em; }}
  .row .label {{ color: #888; }}
  .row .value {{ font-weight: bold; }}
  .row .value.up {{ color: #ef5350; }}
  .row .value.down {{ color: #42a5f5; }}
  
  .ma-row {{ display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #222; }}
  .ma-row:last-child {{ border-bottom: none; }}
  .ma-name {{ color: #ccc; }}
  .ma-val {{ font-weight: bold; color: white; }}
  .ma-status {{ font-size: 0.8em; padding: 2px 6px; border-radius: 4px; }}
  .ma-status.up {{ background: #ef5350; color: white; }}
  .ma-status.down {{ background: #42a5f5; color: white; }}
  
  .kd-container {{ display: flex; align-items: center; gap: 12px; margin-top: 8px; }}
  .kd-bar {{ flex: 1; height: 8px; background: #333; border-radius: 4px; position: relative; }}
  .kd-fill {{ height: 100%; border-radius: 4px; transition: width 0.3s; }}
  .kd-labels {{ display: flex; justify-content: space-between; font-size: 0.75em; color: #666; margin-top: 4px; }}
  .kd-values {{ display: flex; gap: 16px; margin-top: 8px; }}
  .kd-value {{ font-size: 1.2em; font-weight: bold; }}
  
  .verdict {{ background: #1a1a2e; border-radius: 12px; padding: 16px; text-align: center; }}
  .verdict .main {{ font-size: 1.4em; margin-bottom: 8px; }}
  .verdict .detail {{ color: #888; font-size: 0.85em; line-height: 1.6; }}
  
  .trend-bar {{ display: flex; gap: 4px; margin-top: 8px; }}
  .trend-seg {{ flex: 1; height: 4px; border-radius: 2px; }}
  
  .footer {{ text-align: center; color: #555; font-size: 0.75em; margin-top: 16px; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>{a['code']} {a['name']}</h1>
    <div class="subtitle">技術分析儀表板　資料截止：{a['date']}　{a['data_points']}筆歷史</div>
    <div class="price-block">
      <div class="price">{"{:,.1f}".format(a['price'])}</div>
      <div class="chg {'up' if a['chg'] > 0 else 'down' if a['chg'] < 0 else 'flat'}">
        {'▲' if a['chg'] > 0 else '▼' if a['chg'] < 0 else '─'} {a['chg']:+.2f} ({a['chg_pct']:+.2f}%)
      </div>
    </div>
  </div>
  
  <div class="grid">
    <div class="card">
      <h3 class="blue">📊 當前趨勢</h3>
      <div class="row"><span class="label">短期趨勢</span><span class="value">整理格局</span></div>
      <div class="row"><span class="label">均線多頭</span><span class="value {'up' if '多頭' in a['ma_trend'] else 'down' if '空頭' in a['ma_trend'] else ''}">{a['ma_trend']}</span></div>
      <div class="row"><span class="label">KD 狀態</span><span class="value">{a['kd_status']}</span></div>
      <div class="row"><span class="label">MACD</span><span class="value {'up' if a['osc'] > 0 else 'down'}">{a['macd_trend']}</span></div>
      <div style="margin-top:10px; color:#666; font-size:0.8em; line-height:1.5;">
        近期高低點：{a['high20']:.1f} / {a['low20']:.1f}（20日）<br>
        近期漲跌：{'上漲' if a['chg'] > 0 else '下跌' if a['chg'] < 0 else '持平'}
      </div>
    </div>
    
    <div class="card">
      <h3 class="green">📈 移動平均線</h3>
      <div class="ma-row"><span class="ma-name">5MA</span><span class="ma-val">{fmt(a['ma5'])}</span><span class="ma-status {'up' if a['price'] > a['ma5'] else 'down'}">{'▲價上' if a['price'] > a['ma5'] else '▼價下'}</span></div>
      <div class="ma-row"><span class="ma-name">10MA</span><span class="ma-val">{fmt(a['ma10'])}</span><span class="ma-status {'up' if a['price'] > a['ma10'] else 'down'}">{'▲價上' if a['price'] > a['ma10'] else '▼價下'}</span></div>
      <div class="ma-row"><span class="ma-name">20MA</span><span class="ma-val">{fmt(a['ma20'])}</span><span class="ma-status {'up' if a['price'] > a['ma20'] else 'down'}">{'▲價上' if a['price'] > a['ma20'] else '▼價下'}</span></div>
      <div class="ma-row"><span class="ma-name">60MA</span><span class="ma-val">{fmt(a['ma60'])}</span><span class="ma-status {'up' if a['ma60'] and a['price'] > a['ma60'] else 'down'}">{'▲價上' if a['ma60'] and a['price'] > a['ma60'] else '▼價下'}</span></div>
    </div>
    
    <div class="card">
      <h3 class="red">⚡ KD 指標</h3>
      <div class="kd-values">
        <div><span class="kd-value" style="color:{'#ef5350' if a['k'] > a['d'] else '#42a5f5'}">K {a['k']:.1f}</span></div>
        <div><span class="kd-value" style="color:{'#ef5350' if a['d'] < a['k'] else '#42a5f5'}">D {a['d']:.1f}</span></div>
      </div>
      <div style="margin-top:8px; font-size:0.85em; color:{'#ef5350' if a['k'] > a['d'] else '#42a5f5'}">
        {'▶ 黃金交叉：K > D' if a['k'] > a['d'] else '▼ 死亡交叉：K < D'}
      </div>
      <div style="margin-top:4px; font-size:0.8em; color:#888;">
        週期：9日　狀態：{a['kd_status']}
      </div>
    </div>
    
    <div class="card">
      <h3 class="purple">〽️ MACD</h3>
      <div class="row"><span class="label">DIF</span><span class="value">{fmt(a['dif'])}</span></div>
      <div class="row"><span class="label">DEM</span><span class="value">{fmt(a['dem'])}</span></div>
      <div class="row"><span class="label">OSC 柱狀</span><span class="value {'up' if a['osc'] > 0 else 'down'}">{fmt(a['osc'])} ({a['osc_dir']})</span></div>
      <div style="margin-top:8px; font-size:0.8em; color:#888;">
        參數：12/26/9　{'柱往上，動能增強' if a['osc'] > 0 else '柱往下，動能減弱'}
      </div>
    </div>
  </div>
  
  <div class="grid">
    <div class="card">
      <h3>支撐與壓力</h3>
      <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
        <div style="text-align:center;">
          <div style="color:#42a5f5; font-size:0.8em;">壓力 R2</div>
          <div style="font-size:1.3em; font-weight:bold;">{fmt(a['r2'])}</div>
        </div>
        <div style="text-align:center;">
          <div style="color:#ef5350; font-size:0.8em;">壓力 R1</div>
          <div style="font-size:1.3em; font-weight:bold;">{fmt(a['r1'])}</div>
        </div>
        <div style="text-align:center;">
          <div style="color:#888; font-size:0.8em;">樞軸</div>
          <div style="font-size:1.3em; font-weight:bold;">{(a['r1']+a['s1'])/2:.1f}</div>
        </div>
        <div style="text-align:center;">
          <div style="color:#4caf50; font-size:0.8em;">支撐 S1</div>
          <div style="font-size:1.3em; font-weight:bold;">{fmt(a['s1'])}</div>
        </div>
        <div style="text-align:center;">
          <div style="color:#1565c0; font-size:0.8em;">支撐 S2</div>
          <div style="font-size:1.3em; font-weight:bold;">{fmt(a['s2'])}</div>
        </div>
      </div>
      <div style="font-size:0.8em; color:#666; text-align:center;">
        20日區間：{a['low20']:.1f} ～ {a['high20']:.1f}
      </div>
    </div>
    
    <div class="card">
      <h3>綜合判斷</h3>
      <div style="font-size:1.1em; font-weight:bold; margin-bottom:8px;">
        {'✅ 偏多整理' if a['k'] > a['d'] and a['osc'] > 0 else '⚠️ 短線整理' if a['k'] < a['d'] else '🔄 中性觀望'}
      </div>
      <div style="font-size:0.8em; color:#888; line-height:1.6;">
        KD {'黃金交叉' if a['k'] > a['d'] else '死亡交叉'}，{'MACD柱往上' if a['osc'] > 0 else 'MACD柱往下'}，
        均線{'多頭排列' if '多頭' in a['ma_trend'] else '空頭排列' if '空頭' in a['ma_trend'] else '整理中'}。
        {'建議區間操作，逢低承接' if a['k'] < 60 else '注意高檔反轉風險' if a['k'] > 70 else '持續觀望，等待方向明確'}
      </div>
    </div>
  </div>
  
  <div class="footer">
    僅供參考，不構成投資建議　｜　蝦助技術分析系統
  </div>
</div>
</body>
</html>"""

if __name__ == "__main__":
    code = sys.argv[1] if len(sys.argv) > 1 else "2886"
    a = analyze(code)
    html = build_html(a)
    
    out_html = f"{WORKSPACE}/ta_report_{code}.html"
    out_pdf = f"{WORKSPACE}/ta_report_{code}.pdf"
    
    with open(out_html, "w") as f:
        f.write(html)
    print(f"✅ HTML 已儲存: {out_html}")
    
    # Convert to PDF
    os.system(f"wkhtmltopdf --enable-local-file-access --no-stop-slow-scripts {out_html} {out_pdf} 2>/dev/null")
    if os.path.exists(out_pdf):
        size = os.path.getsize(out_pdf) / 1024
        print(f"✅ PDF 已儲存: {out_pdf} ({size:.0f}KB)")
    else:
        print("❌ PDF 生成失敗")
