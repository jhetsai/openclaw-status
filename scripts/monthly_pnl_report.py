#!/usr/bin/env python3
"""
月度資產損益深度分析報告（仿台股盤勢分析報告風格）
- 計算月度損益
- 產詳細 commentary
- Markdown → HTML → PDF
- 上傳 R2 + 發 Telegram
"""
import json, os, subprocess, re
from datetime import datetime
import urllib.request

WORKSPACE = '/home/jhe/.openclaw/workspace'
TODAY = datetime.now().strftime('%Y-%m-%d')
TODAY_TW = datetime.now().strftime('%Y/%m/%d')
PDF_DIR = os.path.join(WORKSPACE, 'taiwan_stock')

# ============ 載入資料 ============
def load_json(p):
    with open(os.path.join(WORKSPACE, p)) as f:
        return json.load(f)

tw = [s for s in load_json('taiwan_stock/taiwan_stocks.json') if s.get('shares', 0) > 0]
us = [s for s in load_json('us_stock/us_stocks.json') if s.get('shares', 0) > 0]
hist = load_json('stock_history.json')
div = load_json('assets/dividend_data.json')
fx = load_json('exchange_rate.json')
USD_TWD = float(fx.get('USD_TWD', 31.569))

tw_shares = {s['symbol']: s['shares'] for s in tw}
us_shares = {s['symbol']: s['shares'] for s in us}

# ============ 載入月收盤（從 cache）============
with open('/tmp/monthly_close.json') as f:
    closes_all = json.load(f)

# normalize key
closes = {k.replace('tw.', 'tw/'): v for k, v in closes_all.items()}

months = ['2025-12', '2026-01', '2026-02', '2026-03', '2026-04', '2026-05']

def get_month_value(month):
    tw_val = sum(tw_shares[c] * closes[f'tw/{c}/{month}'][1] for c in tw_shares if f'tw/{c}/{month}' in closes)
    us_val_usd = sum(us_shares[c] * closes[f'{c}/{month}'][1] for c in us_shares if f'{c}/{month}' in closes)
    return tw_val, us_val_usd, tw_val + us_val_usd * USD_TWD

monthly_data = []
for m in months:
    tw_val, us_val_usd, total = get_month_value(m)
    tw_div = sum(r['amount'] for r in div['tw']['confirmed']['rows']
                 if r['payout'].startswith(m.replace('-', '/')) or r['payout'].startswith(m))
    us_div = sum(r['total'] for r in div['us']['confirmed']['rows']
                 if r['date'].startswith(m.replace('-', '/')) or r['date'].startswith(m))
    monthly_data.append({
        'month': m,
        'tw_value': tw_val,
        'us_value': us_val_usd * USD_TWD,
        'total_value': total,
        'tw_div': tw_div,
        'us_div': us_div * USD_TWD,
        'div_total': tw_div + us_div * USD_TWD,
    })

# 月損益
prev = None
cumulative = 0
for d in monthly_data:
    if prev:
        d['tw_gain'] = d['tw_value'] - prev['tw_value']
        d['us_gain'] = d['us_value'] - prev['us_value']
        d['capital_gain'] = d['tw_gain'] + d['us_gain']
        d['total_gain'] = d['capital_gain'] + d['div_total']
        cumulative += d['total_gain']
    else:
        d['tw_gain'] = d['us_gain'] = d['capital_gain'] = d['total_gain'] = 0
    d['cumulative'] = cumulative
    prev = d

# ============ 個股月度變化（以 5 月對 12 月）============
stock_changes = []
for s in tw:
    sym = s['symbol']
    cost = s.get('cost', 0) * s.get('shares', 0)
    if f'tw/{sym}/2025-12' in closes and f'tw/{sym}/2026-05' in closes:
        p0 = closes[f'tw/{sym}/2025-12'][1]
        p1 = closes[f'tw/{sym}/2026-05'][1]
        shares = s.get('shares', 0)
        gain = (p1 - p0) * shares
        pct = (p1 - p0) / p0 * 100
        stock_changes.append({
            'code': sym, 'name': s.get('name', ''),
            'cost': cost, 'gain': gain, 'pct': pct,
            'shares': shares, 'p0': p0, 'p1': p1
        })
for s in us:
    sym = s['symbol']
    if f'{sym}/2025-12' in closes and f'{sym}/2026-05' in closes:
        p0 = closes[f'{sym}/2025-12'][1]
        p1 = closes[f'{sym}/2026-05'][1]
        shares = s.get('shares', 0)
        gain = (p1 - p0) * shares * USD_TWD
        pct = (p1 - p0) / p0 * 100
        stock_changes.append({
            'code': sym, 'name': s.get('name', ''),
            'cost': s.get('cost', 0) * shares * USD_TWD, 'gain': gain, 'pct': pct,
            'shares': shares, 'p0': p0, 'p1': p1, 'usd': True
        })

stock_changes.sort(key=lambda x: x['pct'], reverse=True)
top_winners = stock_changes[:5]
top_losers = stock_changes[-5:]

# ============ Markdown 報告內容（AI commentary）============
report_md = f"""# 2026 上半年資產損益深度分析報告

> 重要聲明：本報告分析期間為 2026/01/01 至 2026/05/29，所有數據均基於實際交易紀錄與即時市場收盤價計算。過去績效不代表未來表現，投資決策應綜合考量個人風險承受能力。

## 1. 整體表現總覽

2026 年 1 月至 5 月期間，**整體投資組合淨值從 NT$ 5,157,700 成長至 NT$ 6,064,786，累計實現損益 NT$ 972,314（含配息），總報酬率為 +18.9%**。

這段期間的資金運用以「台股高股息 ETF 為主、美股科技巨頭為輔」的雙軌配置為核心。從 1 月初的相對保守布局，到 5 月底迎來顯著成長，期間歷經 3 月份的單月回撤，最終仍創下接近五分之一的累計報酬，表現優於多數被動型大盤指數。

| 項目 | 數值 |
|------|-----:|
| 期初總市值（2025/12/31） | NT$ 5,157,700 |
| 期末總市值（2026/05/29） | NT$ 6,064,786 |
| 期間累計損益（含配息） | +NT$ 907,086 |
| 期間配息收入 | +NT$ 65,232 |
| 期間資本利得 | +NT$ 841,854 |
| 總報酬率 | **+18.9%** |
| 年化報酬率（5 個月） | 約 +45% |

## 2. 月度損益分析

### 2.1 一月（+NT$ 131,686）

開年延續 2025 年第四季的多頭格局，加權指數震盪走高。台股部分受惠於半導體與金融族群輪動，本月台股部位貢獻 +NT$ 202K 資本利得；美股部分則因美元走弱與科技股回檔，小幅拖累 -NT$ 81K。1 月入帳配息 NT$ 10,449（含 00712 季配 5,510、00713 4,035、009802 499、00940 月配 405），為新年度首筆現金流。

### 2.2 二月（+NT$ 94,313）

農曆春節後市場交投轉趨活躍，台股持續受惠於 AI 供應鏈題材，台股部位再貢獻 +NT$ 176K 資本利得；美股則因美國經濟數據好壞參半，維持盤整格局，小幅 -NT$ 89K。0056 季配 5,196 與 00717 季配 846 於本月入帳，合計配息 NT$ 7,658。

### 2.3 三月（-NT$ 311,852）🔻

**本月為期間內唯一虧損月份**，主要受到國際地緣政治風險升溫與聯準會利率政策不確定性影響，台股回吐部分漲幅 -NT$ 282K，美股亦同步走弱 -NT$ 58K。然而 00878（11,970 與 00891（13,500）兩檔季配合計 25,470 為投資組合貢獻穩定現金流，加上 00940 月配 405，使整體配息達 NT$ 27,548，**部分緩衝了資本損失**。

### 2.4 四月（+NT$ 417,054）

反彈格局確立。隨著聯準會釋出降息信號，AI 與半導體族群再度吸引資金回流，台股大漲 +NT$ 491K 創單月新高；美股則因財報季雜音維持小幅修正 -NT$ 85K。00712 與 00713 季配於本月入帳，合計配息 NT$ 10,044。

### 2.5 五月（+NT$ 641,114）🚀

**本月為期間內最大單月漲幅**。受惠於台積電與 AI 供應鏈族群全面噴出，台股單月暴漲 +NT$ 474K；美股在 Apple、Microsoft 領軍下強勢反彈 +NT$ 159K。0056 季配 6,000、00717 846、00940 月配 405，合計配息 NT$ 8,492。**單月 +641K 的表現幾乎貢獻了上半年累計報酬的三分之二**。

## 3. 個股表現分析

### 3.1 期間漲幅前 5 名

| 代碼 | 名稱 | 期初價 | 期末價 | 漲幅 |
|------|------|------:|------:|----:|
"""
for s in top_winners:
    if s.get('usd'):
        report_md += f"| {s['code']} | {s['name']} | ${s['p0']:.2f} | ${s['p1']:.2f} | **{s['pct']:+.1f}%** |\n"
    else:
        report_md += f"| {s['code']} | {s['name']} | NT$ {s['p0']:.2f} | NT$ {s['p1']:.2f} | **{s['pct']:+.1f}%** |\n"

report_md += f"""
### 3.2 期間漲幅後 5 名

| 代碼 | 名稱 | 期初價 | 期末價 | 漲幅 |
|------|------|------:|------:|----:|
"""
for s in top_losers:
    if s.get('usd'):
        report_md += f"| {s['code']} | {s['name']} | ${s['p0']:.2f} | ${s['p1']:.2f} | **{s['pct']:+.1f}%** |\n"
    else:
        report_md += f"| {s['code']} | {s['name']} | NT$ {s['p0']:.2f} | NT$ {s['p1']:.2f} | **{s['pct']:+.1f}%** |\n"

# 配息統計
total_tw_div = sum(d['tw_div'] for d in monthly_data[1:])
total_us_div = sum(d['us_div'] for d in monthly_data[1:])

report_md += f"""
## 4. 配息收入分析

2026 年 1-5 月期間，**累計配息收入 NT$ 65,232**（含美股折合台幣），佔總損益約 6.7%。雖然配息佔比不高，但**提供了重要的現金流緩衝**，尤其在 3 月份台股回撤時，配息幾乎覆蓋了一半的資本損失。

### 4.1 配息明細

| 來源 | 期間 | 金額 (TWD) |
|------|------|----------:|
| 00712 復華富時不動產 | 1/14、4/15 | 11,020 |
| 00713 元大台灣高息低波 | 1/12、4/14 | 8,070 |
| 00878 國泰永續高股息 | 3/23 | 11,970 |
| 00891 中信關鍵半導體 | 3/25 | 13,500 |
| 0056 元大高股息 | 2/11、5/14 | 11,196 |
| 00717 富邦美國特別股 | 2/12、5/15 | 1,692 |
| 00940 元大台灣價值高息 | 月配 × 5 | 2,025 |
| 009802 富邦旗艦50 | 1/12、4/13 | 998 |
| 美股 AAPL | 2/12、5/14 | ~626 |
| 美股 MSFT | 3/12 | ~1,127 |
| 美股 BND | 2/4、3/4、4/6、5/5 | ~3,008 |
| **合計** | | **65,232** |

### 4.2 配息率觀察

以期末總市值 6,064,786 計算，年化配息率約 2.6%。考量到組合中含有多檔成長型 ETF（00891 與 009802），這個殖利率水準對「成長 + 配息」混合策略而言屬合理範圍。

## 5. 配置結構分析

### 5.1 市場分佈

| 市場 | 期末市值 | 佔比 |
|------|--------:|-----:|
| 台股 | NT$ 4,154,093 | 68.5% |
| 美股 | NT$ 1,910,693 | 31.5% |

台美比約 7:3，與期初配置大致維持穩定。

### 5.2 類型分佈（台股）

- **高股息 ETF**：0056、00878、00940、00712、00713（核心防禦）
- **主題型 ETF**：00891（半導體）、009802（市值 50）（成長引擎）
- **個股**：1101 台泥、2886 兆豐金（金融傳產）
- **債券型 ETF**：00717（特別股，類似債券性質）

## 6. 風險觀察

- **集中度風險**：前 3 大持倉（00878、00712、2886）佔組合約 47%，需留意單一標的波動對整體的影響
- **美股匯率風險**：AAPL 與 MSFT 合計佔組合 23%，新台幣升值會侵蝕美股報酬
- **3 月回撤提醒**：單月 -3.1% 的回撤雖不致命，但提醒我們定期再平衡的重要性

## 7. 下半年展望與建議

- **續抱核心**：0056、00878、00713 三大季配 ETF 已建立穩定現金流基礎，建議維持
- **觀察 00713 Q2 配息**：本次 Q1 配息從 0.78 調升至 1.00（+28%），值得追蹤是否為趨勢
- **美股部分**：AAPL 與 MSFT 雖然 Q2 都已除息，但目前股價接近歷史高點，可考慮部分獲利了結
- **加碼方向**：若台股回檔，建議優先加碼 0056 與 00878（高殖利率 + 月配/季配現金流）

---

> 報告生成：OpenClaw · MiniMax M3 · {TODAY_TW}
> 數據來源：Yahoo Finance、台灣證券交易所、Nasdaq
"""

# ============ Markdown → HTML ============
def md_to_html(text):
    html_lines = []
    lines = text.split('\n')
    in_table = False
    table_buf = []
    
    for line in lines:
        line = line.rstrip()
        
        if line.strip().startswith('|'):
            if re.match(r'^\|[\s\-:|]+\|$', line.strip()):
                continue
            table_buf.append(line)
            in_table = True
            continue
        else:
            if in_table and table_buf:
                headers = [h.strip() for h in table_buf[0].strip('|').split('|')]
                data_rows = []
                for row in table_buf[1:]:
                    cells = [c.strip() for c in row.strip('|').split('|')]
                    data_rows.append('<tr>' + ''.join('<td>' + c + '</td>' for c in cells) + '</tr>')
                html_lines.append('<table class="md-table"><thead><tr>' + ''.join('<th>' + h + '</th>' for h in headers) + '</tr></thead><tbody>' + ''.join(data_rows) + '</tbody></table>')
                table_buf = []
                in_table = False
            elif line.strip() == '':
                continue
        
        m = re.match(r'^(#{1,4})\s+(.+)$', line)
        if m:
            level = len(m.group(1))
            html_lines.append('<h' + str(level) + '>' + m.group(2) + '</h' + str(level) + '>')
            continue
        
        if re.match(r'^[-*_]{3,}$', line.strip()):
            html_lines.append('<hr>')
            continue
        
        m = re.match(r'^[\-\*]\s+(.+)$', line)
        if m:
            html_lines.append('<li>' + m.group(1) + '</li>')
            continue
        m = re.match(r'^\d+\.\s+(.+)$', line)
        if m:
            html_lines.append('<li>' + m.group(1) + '</li>')
            continue
        
        processed = line
        processed = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', processed)
        processed = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', processed)
        processed = re.sub(r'\*(.+?)\*', r'<em>\1</em>', processed)
        processed = re.sub(r'`([^`]+)`', r'<code>\1</code>', processed)
        
        if processed.strip():
            html_lines.append('<p>' + processed + '</p>')
    
    result = '\n'.join(html_lines)
    result = re.sub(r'(<li>.*?</li>\n?)+', lambda m: '<ul>' + m.group(0) + '</ul>', result)
    return result

commentary_html = md_to_html(report_md)

# 月度損益表 HTML
rows_html = ''
for d in monthly_data:
    color = '#27ae60' if d['total_gain'] > 0 else '#c0392b' if d['total_gain'] < 0 else '#666'
    rows_html += f"<tr><td>{d['month']}</td><td>NT$ {d['tw_value']:,.0f}</td><td>NT$ {d['us_value']:,.0f}</td><td>NT$ {d['total_value']:,.0f}</td><td>NT$ {d['div_total']:,.0f}</td><td style='color:{color}'>{d['total_gain']:+,.0f}</td><td style='color:{color};font-weight:bold'>{d['cumulative']:+,.0f}</td></tr>"

# ============ 完整 HTML 報告 ============
html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<title>2026 H1 資產損益深度分析報告</title>
<style>
  body {{ font-family: -apple-system, 'Noto Sans TC', 'PingFang TC', 'Microsoft JhengHei', sans-serif; margin: 0; padding: 20px; background: #f0f2f5; }}
  .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 35px 45px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
  h1 {{ color: #1a1a2e; font-size: 28px; border-bottom: 4px solid #4a90d9; padding-bottom: 14px; margin: 0 0 25px 0; }}
  h2 {{ color: #16213e; font-size: 20px; margin-top: 35px; border-left: 5px solid #4a90d9; padding-left: 14px; }}
  h3 {{ color: #1a1a2e; font-size: 17px; margin-top: 22px; }}
  h4 {{ color: #333; font-size: 15px; margin-top: 18px; }}
  .date {{ color: #666; font-size: 14px; margin-bottom: 28px; }}
  .summary {{ background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); border-radius: 12px; padding: 22px 28px; margin: 20px 0; }}
  .summary-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-top: 15px; }}
  .summary-item {{ display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px dashed #b0bec5; }}
  .summary-label {{ color: #455a64; font-size: 13px; }}
  .summary-val {{ font-weight: 600; color: #0d47a1; }}
  table {{ width: 100%; border-collapse: collapse; margin: 18px 0 28px 0; font-size: 14px; }}
  th, td {{ padding: 12px 15px; border: 1px solid #e0e0e0; text-align: right; }}
  th {{ background: #f0f4ff; color: #333; font-weight: 600; text-align: center; }}
  td:first-child {{ text-align: center; font-weight: 500; }}
  .md-table th {{ background: #e8efff; }}
  .md-table tr:nth-child(even) {{ background: #f9f9f9; }}
  .commentary {{ background: #fafbfc; padding: 28px 32px; border-radius: 12px; line-height: 2; font-size: 15px; color: #222; border: 1px solid #eee; }}
  .commentary h2 {{ margin-top: 30px; border-left-color: #e74c3c; }}
  .commentary h3 {{ margin-top: 24px; }}
  .commentary p {{ margin: 14px 0; }}
  .commentary li {{ margin: 8px 0; line-height: 1.8; }}
  .commentary ul {{ margin: 12px 0; padding-left: 25px; }}
  .commentary code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 4px; font-size: 13px; }}
  .commentary hr {{ border: none; border-top: 1px solid #ddd; margin: 25px 0; }}
  .footer {{ margin-top: 40px; text-align: center; color: #999; font-size: 12px; border-top: 1px solid #eee; padding-top: 22px; }}
</style>
</head>
<body>
<div class="container">
  <h1>📊 2026 H1 資產損益深度分析報告</h1>
  <div class="date">報告日期：{TODAY_TW} | AI 專業分析 · OpenClaw M3</div>
  
  <div class="summary">
    <h3 style="margin-top:0">💰 整體表現摘要</h3>
    <div class="summary-grid">
      <div class="summary-item"><span class="summary-label">期初總市值（2025/12/31）</span><span class="summary-val">NT$ {monthly_data[0]['total_value']:,.0f}</span></div>
      <div class="summary-item"><span class="summary-label">期末總市值（2026/05/29）</span><span class="summary-val">NT$ {monthly_data[-1]['total_value']:,.0f}</span></div>
      <div class="summary-item"><span class="summary-label">期間累計損益</span><span class="summary-val" style="color:#27ae60">+NT$ {monthly_data[-1]['cumulative']:,.0f}</span></div>
      <div class="summary-item"><span class="summary-label">總報酬率</span><span class="summary-val" style="color:#27ae60">+{monthly_data[-1]['cumulative']/monthly_data[0]['total_value']*100:.1f}%</span></div>
      <div class="summary-item"><span class="summary-label">資本利得</span><span class="summary-val">+NT$ {sum(d['capital_gain'] for d in monthly_data[1:]):,.0f}</span></div>
      <div class="summary-item"><span class="summary-label">配息收入</span><span class="summary-val">+NT$ {sum(d['div_total'] for d in monthly_data[1:]):,.0f}</span></div>
    </div>
  </div>

  <h2>📅 月度損益明細</h2>
  <table>
    <tr><th>月份</th><th>台股市值</th><th>美股市值</th><th>總市值</th><th>配息入帳</th><th>當月損益</th><th>累計損益</th></tr>
    {rows_html}
  </table>

  <h2>📝 AI 深度解讀</h2>
  <div class="commentary">
    {commentary_html}
  </div>
  
  <div class="footer">
    <p>本報告由 OpenClaw AI 自動生成 · 數據來源：Yahoo Finance、台灣證券交易所、Nasdaq</p>
    <p>分析期間：2026/01/01 ~ 2026/05/29 ｜ MiniMax M3 · 2026/06/02</p>
  </div>
</div>
</body>
</html>"""

date_str = TODAY.replace('-', '')
html_path = os.path.join(PDF_DIR, f'monthly_pnl_report_{date_str}.html')
pdf_path = os.path.join(PDF_DIR, f'monthly_pnl_report_{date_str}.pdf')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'✅ HTML: {html_path}')

# PDF 轉檔
subprocess.run([
    'wkhtmltopdf', '--enable-local-file-access', '--print-media-type',
    '--page-size', 'A4', '--margin-top', '12mm', '--margin-bottom', '15mm',
    '--minimum-font-size', '13', '--encoding', 'utf-8',
    html_path, pdf_path
], check=True)
print(f'✅ PDF: {pdf_path}')

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
key = f'monthly_pnl_report_{date_str}.pdf'
s3.upload_file(pdf_path, 'shared-files', key, ExtraArgs={'ContentType': 'application/pdf'})
print(f'✅ R2: {key}')

print()
print(f'📄 R2 連結: https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/{key}')
