#!/usr/bin/env python3
"""
2026 投資總月報（沿用 monthly_gain_report.html 模板）
- 4 KPI 卡片
- 14 檔逐月損益表 + 今年度欄
- 配息卡片區
- 署名「蝦助出品」
"""
import json, os, subprocess
from datetime import datetime

WORKSPACE = '/home/jhe/.openclaw/workspace'
TODAY = datetime.now().strftime('%Y/%m/%d')

# ============ 載入資料 ============
with open(os.path.join(WORKSPACE, 'taiwan_stock/taiwan_stocks.json')) as f:
    tw = [s for s in json.load(f) if s.get('shares', 0) > 0]
with open(os.path.join(WORKSPACE, 'us_stock/us_stocks.json')) as f:
    us = [s for s in json.load(f) if s.get('shares', 0) > 0]
with open('/tmp/monthly_close.json') as f:
    closes_all = json.load(f)
with open(os.path.join(WORKSPACE, 'assets/dividend_data.json')) as f:
    div = json.load(f)
with open(os.path.join(WORKSPACE, 'exchange_rate.json')) as f:
    fx = json.load(f)
USD_TWD = float(fx.get('USD_TWD', 31.569))
closes = {k.replace('tw.', 'tw/'): v for k, v in closes_all.items()}

# 持股
tw_stocks = {s['symbol']: s for s in tw}
us_stocks = {s['symbol']: s for s in us}
all_stocks = [(s['symbol'], s.get('name', ''), 'TW', s.get('shares', 0)) for s in tw] + \
             [(s['symbol'], s.get('name', ''), 'US', s.get('shares', 0)) for s in us]

months = ['2025-12', '2026-01', '2026-02', '2026-03', '2026-04', '2026-05']

def get_price(code, market, month):
    if market == 'TW':
        key = f'tw/{code}/{month}'
    else:
        key = f'{code}/{month}'
    if key in closes:
        return closes[key][1]
    return None

# 計算每檔每月損益
def calc_stock_monthly_gain(code, market, shares):
    gains = []
    prev_price = None
    for m in months[1:]:  # 1月-5月
        if market == 'TW':
            curr_price = get_price(code, 'TW', m)
        else:
            curr_price = get_price(code, 'US', m)
        if prev_price is not None and curr_price is not None:
            gain = (curr_price - prev_price) * shares
            if market == 'US':
                gain = gain * USD_TWD
            gains.append(gain)
        else:
            gains.append(None)
        if curr_price is not None:
            prev_price = curr_price
    return gains

stock_rows = []
for code, name, market, shares in all_stocks:
    gains = calc_stock_monthly_gain(code, market, shares)
    valid_gains = [g for g in gains if g is not None]
    ytd = sum(valid_gains) if valid_gains else 0
    stock_rows.append({
        'code': code, 'name': name, 'market': market, 'shares': shares,
        'gains': gains, 'ytd': ytd
    })

# 月度合計
month_totals = []
for i in range(len(months) - 1):
    total = sum(r['gains'][i] for r in stock_rows if r['gains'][i] is not None)
    month_totals.append(total)
ytd_total = sum(month_totals)

# 配息
def div_for_month_tw(month):
    slash_m = month.replace('-', '/')
    return sum(r['amount'] for r in div['tw']['confirmed']['rows']
               if r['payout'].startswith(slash_m) or r['payout'].startswith(month))

def div_for_month_us(month):
    slash_m = month.replace('-', '/')
    return sum(r['total'] for r in div['us']['confirmed']['rows']
               if r['date'].startswith(slash_m) or r['date'].startswith(month))

# 已入帳
tw_div_paid = sum(div_for_month_tw(m) for m in months[1:])  # 1-5月
us_div_paid = sum(div_for_month_us(m) for m in months[1:]) * USD_TWD

# 待入帳
tw_div_pending = sum(r['amount'] for r in div['tw']['pending']['rows'])
us_div_pending = sum(r['total'] for r in div['us']['pending']['rows']) * USD_TWD

# 配息合計（含已入+待入）
tw_div_total = tw_div_paid + tw_div_pending
us_div_total = us_div_paid + us_div_pending

# 帳上增量 + 配息總計
gain_plus_div = ytd_total + tw_div_paid + us_div_paid  # 只算已入帳
gain_plus_div_with_pending = ytd_total + tw_div_total + us_div_total  # 含待入帳

# 5月止的最近收盤日
last_close_date = closes.get('tw/0056/2026-05', closes.get('AAPL/2026-05', ('-', 0)))[0]

# 計算起始總市值（用於 % 計算）
def get_starting_value():
    total = 0
    for s in tw:
        sym = s['symbol']
        p = get_price(sym, 'TW', '2025-12')
        if p:
            total += p * s.get('shares', 0)
    for s in us:
        sym = s['symbol']
        p = get_price(sym, 'US', '2025-12')
        if p:
            total += p * s.get('shares', 0) * USD_TWD
    return total

starting_value = get_starting_value()

# ============ 格式化輔助 ============
def fmt_k(n):
    if n is None: return '—'
    if abs(n) >= 1000:
        return f'{n/1000:+.1f}K'
    return f'{n:+.0f}'

def fmt_k_pos_neg(n):
    if n is None: return '—'
    cls = 'pos' if n > 0 else 'neg' if n < 0 else ''
    return f'<td class="{cls}">{fmt_k(n)}</td>'

# 5月份 MVP（找 5 月份賺最多的）
may_gains = [(r['code'], r['gains'][-1]) for r in stock_rows if r['gains'][-1] is not None]
may_gains.sort(key=lambda x: x[1], reverse=True)
may_mvp = may_gains[0] if may_gains else ('', 0)

# 3月份 MVP（最大虧損）
mar_gains = [(r['code'], r['gains'][2]) for r in stock_rows if r['gains'][2] is not None]
mar_gains.sort(key=lambda x: x[1])
mar_mvp = mar_gains[0] if mar_gains else ('', 0)

# ============ HTML ============
rows_html = ''
for r in stock_rows:
    cells = ''.join(fmt_k_pos_neg(g) for g in r['gains'])
    ytd_class = 'pos' if r['ytd'] > 0 else 'neg' if r['ytd'] < 0 else ''
    ytd_text = f'{r["ytd"]/1000:+.1f}K' if abs(r['ytd']) >= 1000 else f'{r["ytd"]:+.0f}'
    rows_html += f'<tr><td class="ln">{r["code"]}</td>{cells}<td class="{ytd_class} ytd">{ytd_text}</td></tr>'

# 月度合計
totals_cells = ''.join(f'<td class="{"pos" if t > 0 else "neg"}">{t/1000:+.1f}K</td>' for t in month_totals)
ytd_total_text = f'{ytd_total/1000:+.1f}K'
rows_html += f'<tr class="tot"><td class="ln">月度合計</td>{totals_cells}<td class="pos ytd">{ytd_total_text}</td></tr>'

# 待入帳各月分組（6月入帳）
tw_pending_jun = sum(r['amount'] for r in div['tw']['pending']['rows']
                     if r['payout'].startswith('2026/06') or r['payout'].startswith('2026-06'))
us_pending_jun = sum(r['total'] for r in div['us']['pending']['rows']
                     if r['date'].startswith('2026/06') or r['date'].startswith('2026-06'))
us_pending_jun_twd = us_pending_jun * USD_TWD

# 5月標籤
mvp5_str = f'{may_mvp[0]} {fmt_k(may_mvp[1])}' if may_mvp[1] else '—'

html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #0f1629; color: #e8ecf5; font-family: 'Segoe UI', 'PingFang TC', system-ui, sans-serif; padding: 15px 20px; }}
.wrapper {{ background: linear-gradient(145deg, #0f1629, #162040); border-radius: 16px; padding: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.5); }}
.header {{ text-align: center; padding-bottom: 12px; border-bottom: 1px solid #1e3a5f; margin-bottom: 12px; }}
.header h1 {{ font-size: 1.15rem; background: linear-gradient(135deg, #00f0ff, #0080ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 700; letter-spacing: 1px; }}
.header .sub {{ color: #7a8ba8; font-size: 0.68rem; margin-top: 4px; }}
.kpi-row {{ display: flex; gap: 8px; justify-content: center; margin: 12px 0; flex-wrap: wrap; }}
.kpi {{ background: #1a2d4a; border-radius: 10px; padding: 8px 14px; text-align: center; border: 1px solid #2a4a6a; min-width: 110px; }}
.kpi .label {{ font-size: 0.58rem; color: #7a8ba8; }}
.kpi .value {{ font-size: 1rem; font-weight: 700; color: #4dff91; }}
.kpi .sub {{ font-size: 0.55rem; color: #7a8ba8; }}
.kpi.orange .value {{ color: #ffc940; }}
.kpi.blue .value {{ color: #00d8ff; }}
.pos {{ color: #4dff91; }} .neg {{ color: #ff5d7d; }}
table {{ width: 100%; border-collapse: collapse; font-size: 0.6rem; margin-bottom: 10px; }}
th {{ background: #1a2d4a; color: #00d8ff; padding: 5px 3px; text-align: center; font-weight: 600; }}
td {{ padding: 3px 3px; text-align: center; border-bottom: 1px solid #111d2e; }}
.ln {{ text-align: left; font-weight: 600; color: #a8c4e8; }}
.tot td {{ color: #00f0ff; border-top: 2px solid #00d8ff; font-weight: 700; background: #162844; }}
.ytd {{ color: #ffd700; font-weight: 700; }}
.section {{ margin-bottom: 12px; }}
.section-title {{ color: #00d8ff; font-size: 0.75rem; font-weight: 700; margin-bottom: 6px; border-left: 3px solid #00d8ff; padding-left: 6px; }}
.div-row {{ display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; }}
.div-card {{ background: #1a2d4a; border-radius: 6px; padding: 6px 10px; border: 1px solid #2a4a6a; }}
.div-card .top {{ font-size: 0.65rem; color: #7a8ba8; }}
.div-card .val {{ font-size: 0.85rem; font-weight: 700; }}
.pending {{ border-color: #3d2a1a; }}
.pending .val {{ color: #ffc940; }}
.footer {{ text-align: center; color: #4a5f7a; font-size: 0.55rem; margin-top: 10px; }}
</style>
</head>
<body>
<div class="wrapper">
<div class="header">
<h1>2026 投資總月報</h1>
<div class="sub">基準：2025/12/31 收盤價｜截至 {last_close_date}｜USD/TWD {USD_TWD:.3f}</div>
</div>

<div class="kpi-row">
<div class="kpi"><div class="label">帳上增量</div><div class="value pos">+{ytd_total/1000:.1f}K</div><div class="sub">+{ytd_total/starting_value*100:.1f}%</div></div>
<div class="kpi orange"><div class="label">配息已入帳</div><div class="value">+{(tw_div_paid+us_div_paid)/1000:.1f}K</div><div class="sub">台+美股</div></div>
<div class="kpi orange"><div class="label">配息待入帳</div><div class="value">+{(tw_div_pending+us_div_pending)/1000:.1f}K</div><div class="sub">6-7月入帳</div></div>
<div class="kpi blue"><div class="label">增值+配息總計</div><div class="value">+{gain_plus_div_with_pending/1000:.1f}K</div><div class="sub">含待入帳</div></div>
</div>

<div class="section">
<div class="section-title">📈 各月帳上增量（當月 vs 上月底）</div>
<table>
<thead><tr><th>股票</th><th>1月</th><th>2月</th><th>3月</th><th>4月</th><th>5月</th><th>今年度</th></tr></thead>
<tbody>
{rows_html}
</tbody>
</table>
</div>

<div class="section">
<div class="section-title">💰 2026配息（已入帳+待入帳）</div>
<div class="div-row">
<div class="div-card"><div class="top">台股已入帳</div><div class="val pos">+{tw_div_paid:,}</div></div>
<div class="div-card"><div class="top">美股實收(TWD)</div><div class="val pos">+{us_div_paid:,.0f}</div></div>
<div class="div-card pending"><div class="top">台股待入(6-7月)</div><div class="val">+{tw_div_pending:,}</div></div>
<div class="div-card pending"><div class="top">美股待入(6月)</div><div class="val">+{us_div_pending:,.0f}</div></div>
<div class="div-card"><div class="top">合計</div><div class="val" style="color:#ffd700">+{(tw_div_total+us_div_total):,.0f}</div></div>
</div>
</div>

<div class="footer">📊 持股總覽｜🦞 蝦助出品｜{TODAY}</div>
</div>
</body>
</html>"""

# ============ 輸出 ============
date_str = datetime.now().strftime('%Y%m%d')
out_html = os.path.join(WORKSPACE, 'stock', f'monthly_gain_report_{date_str}.html')
out_pdf = os.path.join(WORKSPACE, 'stock', f'monthly_gain_report_{date_str}.pdf')

with open(out_html, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'✅ HTML: {out_html}')

subprocess.run(['wkhtmltopdf', '--enable-local-file-access', '--page-size', 'A4',
                '--margin-top', '8mm', '--margin-bottom', '8mm', out_html, out_pdf], check=True)
print(f'✅ PDF: {out_pdf}')

# 上傳 R2
import boto3
with open(os.path.expanduser('~/.api_keys')) as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            os.environ[k] = v
s3 = boto3.client('s3', endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
    aws_access_key_id=os.environ.get('R2_ACCESS_KEY'),
    aws_secret_access_key=os.environ.get('R2_SECRET_KEY'))
key = f'stock/monthly_gain_report_{date_str}.pdf'
s3.upload_file(out_pdf, 'shared-files', key, ExtraArgs={'ContentType': 'application/pdf'})
print(f'✅ R2: {key}')

# 順便也上傳到 posters/ 保持跟舊版位置一致
s3.upload_file(out_pdf, 'shared-files', f'posters/stock_monthly_profit_2026_v3.pdf', ExtraArgs={'ContentType': 'application/pdf'})

print()
print(f'📄 R2 連結: https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/{key}')
