#!/usr/bin/env python3
"""
月報產出腳本：每月底跑一次，產生 PNG 圖表 + HTML 報告 + PDF 海報
- 圖表: matplotlib 仿 monthly_pnl_chart_v3.png 風格
- HTML: 多頁儀表板（總覽、每月圖、配息明細）
- PDF: wkhtmltopdf 轉 A4 橫向
"""
import json
import subprocess
import os
from datetime import datetime, timedelta

WORKSPACE = '/home/jhe/.openclaw/workspace'
TODAY = datetime.now().strftime('%Y-%m-%d')
TODAY_TW = datetime.now().strftime('%Y/%m/%d')

# ============ 載入資料 ============
def load_json(path):
    with open(os.path.join(WORKSPACE, path)) as f:
        return json.load(f)

tw = [s for s in load_json('taiwan_stock/taiwan_stocks.json') if s.get('shares', 0) > 0]
us = [s for s in load_json('us_stock/us_stocks.json') if s.get('shares', 0) > 0]
hist = load_json('stock_history.json')
div = load_json('assets/dividend_data.json')
fx = load_json('exchange_rate.json')
USD_TWD = float(fx.get('USD_TWD', 31.569))

tw_shares = {s['symbol']: s['shares'] for s in tw}
us_shares = {s['symbol']: s['shares'] for s in us}
tw_codes = list(tw_shares.keys())
us_codes = list(us_shares.keys())

# ============ 取每月底收盤價（從 Yahoo 抓缺月）============
def fetch_yahoo_closes(codes, market_suffix, months):
    """從 Yahoo 抓每月最後交易日收盤"""
    cache_path = '/tmp/monthly_close.json'
    cached = {}
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            cached = json.load(f)
    results = {}
    for code in codes:
        for m in months:
            key = f'{market_suffix}{code}/{m}'
            if key in cached:
                results[key] = cached[key]
                continue
    missing_codes = [c for c in codes if not any(f'{market_suffix}{c}/{m}' in results for m in months)]
    # Yahoo URL suffix: TW = ".TW", US = ""
    yahoo_suffix = '.TW' if market_suffix == 'tw/' else ''
    for code in missing_codes:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}{yahoo_suffix}?interval=1d&range=6mo'
        try:
            r = subprocess.run(['curl', '-s', '--max-time', '8', '-H', 'User-Agent: Mozilla/5.0', url],
                              capture_output=True, text=True, timeout=10)
            data = json.loads(r.stdout)
            result = data['chart']['result'][0]
            ts = result['timestamp']
            closes = result['indicators']['quote'][0]['close']
            for i, t in enumerate(ts):
                d = datetime.fromtimestamp(t).strftime('%Y-%m-%d')
                month_key = d[:7]
                key = f'{market_suffix}{code}/{month_key}'
                if month_key in months and key not in results:
                    results[key] = (d, closes[i])
        except Exception as e:
            print(f'{market_suffix}{code} FAIL: {e}')
    with open(cache_path, 'w') as f:
        json.dump(results, f, indent=2)
    return results

# 統一 key 格式：convert tw. → tw/
def normalize_keys(d):
    out = {}
    for k, v in d.items():
        out[k] = v
    return out

# 6 個月：基準 + 5 個月報告
months = ['2025-12', '2026-01', '2026-02', '2026-03', '2026-04', '2026-05']
closes = fetch_yahoo_closes(tw_codes, 'tw/', months)
closes.update(fetch_yahoo_closes(us_codes, '', months))
closes = normalize_keys(closes)

# ============ 計算每月市值 ============
def get_month_value(month):
    tw_val = sum(tw_shares[c] * closes[f'tw/{c}/{month}'][1] for c in tw_codes if f'tw/{c}/{month}' in closes)
    us_val_usd = sum(us_shares[c] * closes[f'{c}/{month}'][1] for c in us_codes if f'{c}/{month}' in closes)
    return {
        'tw': tw_val,
        'us_usd': us_val_usd,
        'us_twd': us_val_usd * USD_TWD,
        'total': tw_val + us_val_usd * USD_TWD
    }

monthly = {m: get_month_value(m) for m in months}

# 配息（兩種日期格式都處理）
def div_for_month(month):
    slash_m = month.replace('-', '/')
    tw_total = sum(r['amount'] for r in div['tw']['confirmed']['rows']
                   if r['payout'].startswith(slash_m) or r['payout'].startswith(month))
    us_total_usd = sum(r['total'] for r in div['us']['confirmed']['rows']
                       if r['date'].startswith(slash_m) or r['date'].startswith(month))
    return tw_total, us_total_usd * USD_TWD, tw_total + us_total_usd * USD_TWD

# 計算每月損益
report = []
prev_value = None
cumulative = 0
for i, m in enumerate(months):
    v = monthly[m]['total']
    tw_div, us_div, total_div = div_for_month(m)
    if i == 0:
        capital_gain = 0
        total_gain = 0
    else:
        capital_gain = v - prev_value
        total_gain = capital_gain + total_div
        cumulative += total_gain
    report.append({
        'month': m,
        'tw_value': monthly[m]['tw'],
        'us_value': monthly[m]['us_twd'],
        'total_value': v,
        'div': total_div,
        'capital_gain': capital_gain,
        'total_gain': total_gain,
        'cumulative': cumulative,
    })
    prev_value = v

# ============ 繪圖（仿 v3.png 風格）============
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

report_months = report[1:]  # 排除基準月
month_labels = [r['month'][5:] + '/' + r['month'][2:4] for r in report_months]
tw_gains = [r['capital_gain'] * (r['tw_value'] - (report[report_months.index(r)]['tw_value'] - r['capital_gain'] if report_months.index(r) > 0 else 0)) / max(1, r['tw_value'] + (report[report_months.index(r)]['tw_value'] - r['capital_gain'] if report_months.index(r) > 0 else 0)) for r in report_months]
# 簡化：直接用 month-over-month change
tw_changes = []
us_changes = []
cumulative_pnl = []
cum = 0
prev_tw = report[0]['tw_value']
prev_us = report[0]['us_value']
for r in report_months:
    tw_changes.append(r['tw_value'] - prev_tw)
    us_changes.append(r['us_value'] - prev_us)
    cum += r['total_gain']
    cumulative_pnl.append(cum)
    prev_tw = r['tw_value']
    prev_us = r['us_value']

fig, ax1 = plt.subplots(figsize=(13, 6.5))
x = np.arange(len(month_labels))
width = 0.35

bars1 = ax1.bar(x - width/2, [v/1000 for v in tw_changes], width, label='TW Stocks (K NTD)', color='#c0504d')
bars2 = ax1.bar(x + width/2, [v/1000 for v in us_changes], width, label='US Stocks (K NTD)', color='#4f81bd')

ax1.set_ylabel('Monthly Profit/Loss (K NTD)', fontsize=11)
ax1.set_xticks(x)
ax1.set_xticklabels(month_labels)
ax1.axhline(y=0, color='gray', linestyle='--', linewidth=0.7)
ax1.grid(axis='y', alpha=0.3)
ax1.legend(loc='upper left')

# 標柱頂值
for bar, val in zip(bars1, tw_changes):
    h = bar.get_height()
    ax1.annotate(f'{val/1000:+,.0f}', xy=(bar.get_x() + bar.get_width()/2, h),
                 xytext=(0, 5 if h >= 0 else -15), textcoords='offset points',
                 ha='center', fontsize=9, fontweight='bold')
for bar, val in zip(bars2, us_changes):
    h = bar.get_height()
    ax1.annotate(f'{val/1000:+,.0f}', xy=(bar.get_x() + bar.get_width()/2, h),
                 xytext=(0, 5 if h >= 0 else -15), textcoords='offset points',
                 ha='center', fontsize=9, fontweight='bold', color='#1f497d')

ax2 = ax1.twinx()
ax2.plot(x, [v/1000 for v in cumulative_pnl], color='#2ca02c', marker='o', linewidth=2.5, label='Total P&L')
ax2.set_ylabel('Cumulative P&L (K TWD)', fontsize=11)
for xi, val in zip(x, cumulative_pnl):
    ax2.annotate(f'+{val/1000:,.0f}', xy=(xi, val/1000), xytext=(8, 0), textcoords='offset points',
                 fontsize=10, color='#2ca02c', fontweight='bold',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#2ca02c'))
ax2.legend(loc='upper right')

total_cost = sum(s.get('total_cost', s['shares'] * s['cost']) for s in tw + us)
total_return_pct = cumulative / report[0]['total_value'] * 100

plt.title(f'Portfolio Monthly P&L Report (Jan-May 2026)\n'
          f'Total Return: +{total_return_pct:.1f}% | Cost: NT$ {total_cost:,.0f}',
          fontsize=14, fontweight='bold', pad=15)
plt.figtext(0.5, 0.01, f'Generated: {TODAY}', ha='center', fontsize=8, color='gray')
plt.tight_layout(rect=[0, 0.02, 1, 1])
chart_path = os.path.join(WORKSPACE, 'posters', 'monthly_pnl_chart_v4.png')
plt.savefig(chart_path, dpi=120, bbox_inches='tight', facecolor='white')
chart_uri = 'file://' + chart_path
plt.close()
print(f'✅ 圖表: {chart_path}')

# ============ HTML 報告（多頁）============
total_cost = sum(s.get('total_cost', s['shares'] * s['cost']) for s in tw + us)
total_return_pct = cumulative / report[0]['total_value'] * 100

# 摘要
summary_html = f"""
<div class="kpi-row">
  <div class="kpi"><div class="kpi-val">NT$ {report[0]['total_value']:,.0f}</div><div class="kpi-lbl">2025/12 基準</div></div>
  <div class="kpi"><div class="kpi-val">NT$ {report[-1]['total_value']:,.0f}</div><div class="kpi-lbl">2026/05 收盤</div></div>
  <div class="kpi"><div class="kpi-val" style="color:#2ca02c">+{cumulative:,.0f}</div><div class="kpi-lbl">累計損益 (TWD)</div></div>
  <div class="kpi"><div class="kpi-val" style="color:#2ca02c">+{total_return_pct:.1f}%</div><div class="kpi-lbl">總報酬率</div></div>
</div>
"""

# 月度明細表
rows_html = ''
for r in report[1:]:
    color = '#2ca02c' if r['total_gain'] > 0 else '#c0392b' if r['total_gain'] < 0 else '#666'
    rows_html += f"""
    <tr>
      <td>{r['month']}</td>
      <td>NT$ {r['tw_value']:,.0f}</td>
      <td>NT$ {r['us_value']:,.0f}</td>
      <td>NT$ {r['total_value']:,.0f}</td>
      <td>NT$ {r['div']:,.0f}</td>
      <td style="color:{color}">{r['total_gain']:+,.0f}</td>
      <td style="color:{color};font-weight:bold">{r['cumulative']:+,.0f}</td>
    </tr>
    """

# 配息明細
div_rows_html = ''
for r in div['tw']['confirmed']['rows'] + div['us']['confirmed']['rows']:
    if 'code' in r:
        if 'date' in r:  # US
            div_rows_html += f"<tr><td>{r['code']}</td><td>US</td><td>{r['date']}</td><td>${r['total']:.2f}</td></tr>"
        else:  # TW
            div_rows_html += f"<tr><td>{r['code']}</td><td>TW</td><td>{r['payout']}</td><td>NT$ {r['amount']:,.0f}</td></tr>"

html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<title>2026 H1 資產損益月報</title>
<style>
@page {{ size: A4 landscape; margin: 12mm; }}
body {{ font-family: "Microsoft JhengHei", -apple-system, sans-serif; margin: 0; color: #1a1a2e; background: #f8f9fa; }}
.page {{ background: white; padding: 20px 30px; margin: 0 auto; max-width: 1200px; min-height: 750px; page-break-after: always; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
.page:last-child {{ page-break-after: auto; }}
h1 {{ color: #0d47a1; border-bottom: 3px solid #1976d2; padding-bottom: 10px; font-size: 24px; margin: 0 0 18px 0; }}
h2 {{ color: #1976d2; font-size: 18px; border-left: 5px solid #1976d2; padding-left: 12px; margin: 20px 0 12px 0; }}
.kpi-row {{ display: flex; gap: 15px; margin: 18px 0; }}
.kpi {{ flex: 1; background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); border-radius: 10px; padding: 18px 15px; text-align: center; }}
.kpi-val {{ font-size: 22px; font-weight: bold; color: #0d47a1; }}
.kpi-lbl {{ font-size: 12px; color: #666; margin-top: 5px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin: 10px 0; }}
th, td {{ border: 1px solid #d0d0d0; padding: 8px 12px; text-align: right; }}
th {{ background: #1976d2; color: white; text-align: center; }}
td:first-child {{ text-align: left; }}
tr:nth-child(even) {{ background: #f8f9fa; }}
.chart {{ width: 100%; margin: 10px 0; }}
.footer {{ text-align: center; color: #999; font-size: 11px; margin-top: 20px; padding-top: 10px; border-top: 1px solid #ddd; }}
</style>
</head>
<body>

<div class="page">
<h1>📊 2026 H1 資產損益月報</h1>
<p style="color:#666;font-size:12px">報告日期：{TODAY_TW} ｜ 期間：2026/01/01 ~ 2026/05/29</p>
{summary_html}
<h2>📅 月度損益明細</h2>
<table>
<tr><th>月份</th><th>台股市值</th><th>美股市值</th><th>總市值</th><th>配息入帳</th><th>當月損益</th><th>累計損益</th></tr>
{rows_html}
</table>
<div class="footer">Generated by OpenClaw · MiniMax M3 · 2026/06/02</div>
</div>

<div class="page">
<h1>📈 月度損益圖表</h1>
<p style="color:#666;font-size:12px">柱狀圖為當月資本利得（台股紅、美股藍）；綠色折線為累計損益（含配息）</p>
<img class="chart" src="{chart_uri}">
<div class="footer">page 2 / 3</div>
</div>

<div class="page">
<h1>💰 2026 配息明細</h1>
<table>
<tr><th>代碼</th><th>市場</th><th>入帳日</th><th>金額</th></tr>
{div_rows_html}
</table>
<p style="color:#666;font-size:12px;margin-top:20px">合計：NT$ {sum(r['amount'] for r in div['tw']['confirmed']['rows']):,.0f} + US${sum(r['total'] for r in div['us']['confirmed']['rows']):.2f}</p>
<div class="footer">page 3 / 3</div>
</div>

</body>
</html>"""

html_path = os.path.join(WORKSPACE, 'posters', 'monthly_pnl_report.html')
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'✅ HTML: {html_path}')

# ============ PDF 轉檔 ============
pdf_path = os.path.join(WORKSPACE, 'posters', 'stock_monthly_profit_2026_v2.pdf')
subprocess.run(['wkhtmltopdf', '--enable-local-file-access', '--orientation', 'Landscape',
                '--page-size', 'A4', html_path, pdf_path], check=True)
print(f'✅ PDF: {pdf_path}')

# ============ 上傳 R2 ============
import boto3
with open(os.path.expanduser('~/.api_keys')) as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            os.environ[k] = v
s3 = boto3.client('s3', endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
    aws_access_key_id=os.environ.get('R2_ACCESS_KEY'),
    aws_secret_access_key=os.environ.get('R2_SECRET_KEY'))
for src, key in [(chart_path, 'posters/monthly_pnl_chart_v4.png'),
                  (pdf_path, 'posters/stock_monthly_profit_2026_v2.pdf')]:
    s3.upload_file(src, 'shared-files', key, ExtraArgs={'ContentType': 'image/png' if 'png' in key else 'application/pdf'})
    print(f'✅ R2: {key}')

print()
print('=== 完成 ===')
print(f'圖表: https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/posters/monthly_pnl_chart_v4.png')
print(f'PDF: https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/posters/stock_monthly_profit_2026_v2.pdf')
