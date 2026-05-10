#!/usr/bin/env python3
"""
持股快報生成腳本
用法: python3 stock-quick-report.py
"""

import json
import os
from datetime import datetime

# R2 upload function
def upload_r2(local_path):
    import boto3
    ACCESS_KEY = os.environ.get('R2_ACCESS_KEY')
    SECRET_KEY = os.environ.get('R2_SECRET_KEY')
    ENDPOINT = 'https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com'
    BUCKET = 'shared-files'
    
    s3 = boto3.client('s3', endpoint_url=ENDPOINT, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
    filename = os.path.basename(local_path)
    s3.upload_file(local_path, BUCKET, filename)
    return f"https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/{filename}"

def format_money(n):
    return f"{int(n):,}"

def generate_report():
    # Read Taiwan stocks
    tw_path = '/home/jhe/.openclaw/workspace/taiwan_stock/taiwan_stocks.json'
    with open(tw_path) as f:
        tw_data = json.load(f)
    
    # Read US stocks
    us_path = '/home/jhe/.openclaw/workspace/us_stock/us_stocks.json'
    with open(us_path) as f:
        us_data = json.load(f)
    
    # Read US prices for exchange rate
    prices_path = '/home/jhe/.openclaw/workspace/us_stock/us_prices.json'
    with open(prices_path) as f:
        us_prices = json.load(f)
    
    exchange_rate = 31.935
    # Load dynamic exchange rate (臺灣銀行即期匯率本行買入)
    _exch = '/home/jhe/.openclaw/workspace/exchange_rate.json'
    if os.path.exists(_exch):
        with open(_exch) as f:
            _d = json.load(f)
            exchange_rate = float(_d.get('USD_TWD', 31.935))

    now = datetime.now()
    date_str = now.strftime("%Y/%m/%d")
    time_str = now.strftime("%H:%M")
    
    # Calculate Taiwan stock stats
    tw_total_cost = 0
    tw_total_value = 0
    tw_total_gain = 0
    tw_daily_change = 0
    
    for s in tw_data:
        cost = s.get('total_cost', s['shares'] * s['cost'])
        value = s.get('market_value', s['shares'] * s['price'])
        prev = s.get('prev_price', s['price'])
        
        tw_total_cost += cost
        tw_total_value += value
        tw_total_gain += (value - cost)
        tw_daily_change += (s['price'] - prev) * s['shares']
    
    tw_gain_pct = (tw_total_gain / tw_total_cost * 100) if tw_total_cost > 0 else 0
    tw_daily_pct = (tw_daily_change / (tw_total_value - tw_daily_change) * 100) if tw_total_value > tw_daily_change else 0
    
    # Calculate US stock stats
    us_total_cost_twd = 0
    us_total_value_twd = 0
    us_total_gain_twd = 0
    us_daily_change_twd = 0
    
    for s in us_data:
        cost_usd = s['shares'] * s['cost']
        value_usd = s['shares'] * s['price']
        prev_usd = s.get('prev', s['price'])
        
        cost_twd = cost_usd * exchange_rate
        value_twd = value_usd * exchange_rate
        
        us_total_cost_twd += cost_twd
        us_total_value_twd += value_twd
        us_total_gain_twd += (value_twd - cost_twd)
        us_daily_change_twd += (value_usd - prev_usd) * s['shares'] * exchange_rate
    
    us_gain_pct = (us_total_gain_twd / us_total_cost_twd * 100) if us_total_cost_twd > 0 else 0
    us_daily_pct = (us_daily_change_twd / (us_total_value_twd - us_daily_change_twd) * 100) if us_total_value_twd > us_daily_change_twd else 0
    
    # Combined stats
    total_cost = tw_total_cost + us_total_cost_twd
    total_value = tw_total_value + us_total_value_twd
    total_gain = tw_total_gain + us_total_gain_twd
    total_daily = tw_daily_change + us_daily_change_twd
    gain_pct = (total_gain / total_cost * 100) if total_cost > 0 else 0
    daily_pct = (total_daily / (total_value - total_daily) * 100) if total_value > total_daily else 0
    
    # Top gainers/losers
    tw_sorted = sorted(tw_data, key=lambda x: (x['price'] - x.get('prev_price', x['price'])) / x.get('prev_price', x['price']) * 100, reverse=True)
    
    # Find ex-dividend stocks
    ex_div_stocks = [s for s in tw_data if s.get('exDate')]
    
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>持股快報 {date_str}</title>
<style>
  body {{ font-family: -apple-system, sans-serif; background: #0f0f1a; color: #fff; padding: 20px; margin: 0; }}
  .card {{ background: #1a1a2e; border-radius: 16px; padding: 20px; margin-bottom: 15px; }}
  .header {{ text-align: center; margin-bottom: 20px; }}
  .header h1 {{ color: #667eea; margin: 0; font-size: 1.5em; }}
  .header p {{ color: #888; margin: 5px 0 0; font-size: 0.9em; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }}
  .kpi {{ background: #252540; border-radius: 12px; padding: 15px; }}
  .kpi-label {{ font-size: 0.75em; color: #888; margin-bottom: 5px; }}
  .kpi-value {{ font-size: 1.3em; font-weight: 700; }}
  .kpi-sub {{ font-size: 0.7em; color: #666; margin-top: 3px; }}
  .green {{ color: #22c55e; }}
  .red {{ color: #ef4444; }}
  .section-title {{ font-size: 0.9em; color: #667eea; margin: 15px 0 10px; font-weight: 600; }}
  .stock-list {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 8px; }}
  .stock-item {{ background: #252540; border-radius: 8px; padding: 10px; }}
  .stock-name {{ font-size: 0.8em; color: #aaa; margin-bottom: 3px; }}
  .stock-price {{ font-size: 1em; font-weight: 600; }}
  .stock-change {{ font-size: 0.75em; margin-top: 2px; }}
  .divider {{ height: 1px; background: #333; margin: 15px 0; }}
  .ex-div {{ background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 8px; padding: 10px; }}
  .ex-div-title {{ color: #f59e0b; font-size: 0.85em; font-weight: 600; margin-bottom: 5px; }}
  .ex-div-item {{ font-size: 0.8em; color: #ccc; }}
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <h1>📊 持股快報</h1>
    <p>{date_str} {time_str} 更新</p>
  </div>
  
  <div class="kpi-grid">
    <div class="kpi">
      <div class="kpi-label">總市值</div>
      <div class="kpi-value">${format_money(total_value)}</div>
      <div class="kpi-sub">成本 ${format_money(total_cost)}</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">今日損益</div>
      <div class="kpi-value {'green' if total_daily >= 0 else 'red'}">{'+' if total_daily >= 0 else ''}{format_money(total_daily)}</div>
      <div class="kpi-sub {'green' if total_daily >= 0 else 'red'}">{'▲' if total_daily >= 0 else '▼'} {abs(daily_pct):.2f}%</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">累計報酬</div>
      <div class="kpi-value {'green' if total_gain >= 0 else 'red'}">{'+' if total_gain >= 0 else ''}{format_money(total_gain)}</div>
      <div class="kpi-sub {'green' if total_gain >= 0 else 'red'}">報酬率 {abs(gain_pct):.2f}%</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">總持股</div>
      <div class="kpi-value">{len(tw_data) + len(us_data)} 檔</div>
      <div class="kpi-sub">台{len(tw_data)} 美{len(us_data)}</div>
    </div>
  </div>
</div>

<div class="card">
  <div class="kpi-grid">
    <div class="kpi">
      <div class="kpi-label">台股</div>
      <div class="kpi-value">${format_money(tw_total_value)}</div>
      <div class="kpi-sub {'green' if tw_daily_change >= 0 else 'red'}">今日 {'+' if tw_daily_change >= 0 else ''}{format_money(tw_daily_change)}</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">美股</div>
      <div class="kpi-value">${format_money(us_total_value_twd)}</div>
      <div class="kpi-sub {'green' if us_daily_change_twd >= 0 else 'red'}">今日 {'+' if us_daily_change_twd >= 0 else ''}{format_money(us_daily_change_twd)}</div>
    </div>
  </div>
</div>
"""

    # Ex-dividend alert
    if ex_div_stocks:
        html += '<div class="card"><div class="ex-div-title">⚠️ 近期除息</div>'
        for s in ex_div_stocks:
            ex_date = s.get('exDate', '')
            div_amount = s.get('divAmount', 0)
            html += f'<div class="ex-div-item">• {s["symbol"]} {s["name"]} 除息日:{ex_date} 配息 {div_amount}元</div>'
        html += '</div>'

    # Top movers
    html += '<div class="card"><div class="section-title">📈 台股今日表現</div><div class="stock-list">'
    for s in tw_sorted[:6]:
        prev = s.get('prev_price', s['price'])
        chg = s['price'] - prev
        chg_pct = (chg / prev * 100) if prev > 0 else 0
        html += f"""<div class="stock-item">
  <div class="stock-name">{s['symbol']} {s['name'][:4]}</div>
  <div class="stock-price">{s['price']}</div>
  <div class="stock-change {'green' if chg >= 0 else 'red'}">{'▲' if chg >= 0 else '▼'} {abs(chg_pct):.2f}%</div>
</div>"""
    html += '</div></div>'

    # US stocks
    html += '<div class="card"><div class="section-title">💵 美股報價</div><div class="stock-list">'
    for s in us_data:
        html += f"""<div class="stock-item">
  <div class="stock-name">{s['symbol']} {s['name'][:6]}</div>
  <div class="stock-price">${s['price']}</div>
  <div class="stock-change">成本 ${s['cost']}</div>
</div>"""
    html += '</div></div>'

    html += '</body></html>'
    
    # Save
    out_path = '/home/jhe/.openclaw/workspace/stock_quick_report.html'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    # Upload
    url = upload_r2(out_path)
    print(f"✅ 持股快報已生成: {url}")
    return url

if __name__ == '__main__':
    generate_report()