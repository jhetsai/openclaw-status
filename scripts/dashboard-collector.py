#!/usr/bin/env python3
"""
儀表板資料收集器
- 抓 /sys（CPU/RAM/磁碟/API 用量）
- 抓 portfolio（持股現價 + 總市值）
- 產生 JSON 給 ESP32 抓
- 產生 HTML 給手機預覽
- 上傳到 R2（公開 CDN）

執行：python3 dashboard-collector.py
Cron：每 1 分鐘
"""
import json
import os
import subprocess
import urllib.request
import boto3
from datetime import datetime, timezone, timedelta
from html import escape

# ============================================================
# 設定
# ============================================================
R2_ENDPOINT = 'https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com'
R2_ACCESS_KEY = os.environ.get('R2_ACCESS_KEY', '')
R2_SECRET_KEY = os.environ.get('R2_SECRET_KEY', '')
R2_BUCKET = 'shared-files'
R2_PUBLIC_URL = 'https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev'

# Load api_keys if exists
_api_keys_file = os.path.expanduser('~/.api_keys')
if os.path.exists(_api_keys_file):
    with open(_api_keys_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line.startswith('R2_ACCESS_KEY='):
                R2_ACCESS_KEY = _line.split('=', 1)[1].strip()
            elif _line.startswith('R2_SECRET_KEY='):
                R2_SECRET_KEY = _line.split('=', 1)[1].strip()

# 持股設定（同步自 MEMORY.md 2026-06-04）
TW_STOCKS = [
    ('0056.TW', '0056', '元大高股息', 6000, 26.20),
    ('00692.TW', '00692', '富邦公司治理', 10074, 21.11),
    ('00712.TW', '00712', '復華富時不動產', 29000, 9.02),
    ('00713.TW', '00713', '元大台灣高息低波', 5173, 34.03),
    ('00717.TW', '00717', '富邦美國特別股', 6000, 13.91),
    ('00878.TW', '00878', '國泰永續高股息', 28500, 7.36),
    ('00891.TW', '00891', '中信關鍵半導體', 18000, 6.89),
    ('00940.TW', '00940', '元大台灣價值高息', 9000, 8.30),
    ('009802.TW', '009802', '富邦旗艦50', 5427, 8.99),
    ('1101.TW', '1101', '台泥', 5499, 38.64),
    ('2886.TW', '2886', '兆豐金', 10664, 24.33),
]
US_STOCKS = [
    ('AAPL', 'AAPL', '蘋果', 105, 145.02),
    ('MSFT', 'MSFT', '微軟', 55, 263.51),
    ('BND', 'BND', '債券ETF', 118, 73.22),
]

# ============================================================
# 1. 抓 /sys 系統狀態
# ============================================================
def get_cpu_pct():
    try:
        out = subprocess.check_output(
            "top -bn1 | grep 'Cpu' | head -1 | awk '{print $2}'",
            shell=True, timeout=3
        ).decode().strip()
        return float(out)
    except Exception:
        return 0.0

def get_ram_info():
    try:
        out = subprocess.check_output("free -m | grep Mem", shell=True, timeout=3).decode()
        parts = out.split()
        total = int(parts[1])
        used = int(parts[2])
        return used, total, used / total * 100
    except Exception:
        return 0, 0, 0.0

def get_disk_pct():
    try:
        out = subprocess.check_output("df -h / | tail -1", shell=True, timeout=3).decode()
        return float(out.split()[4].rstrip('%'))
    except Exception:
        return 0.0

def get_openrouter_usage():
    try:
        key = os.environ.get('OPENROUTER_API_KEY', '')
        if not key:
            return 0.0
        req = urllib.request.Request(
            'https://openrouter.ai/api/v1/auth/key',
            headers={'Authorization': f'Bearer {key}'}
        )
        d = json.loads(urllib.request.urlopen(req, timeout=5).read())
        return d['data'].get('usage', 0.0)
    except Exception:
        return 0.0

def get_brave_count():
    try:
        path = os.path.expanduser('~/.openclaw/brave_search_usage.json')
        if os.path.exists(path):
            with open(path) as f:
                d = json.load(f)
            return d.get('count', 0)
    except Exception:
        pass
    return 0

def collect_sys():
    now = datetime.now(timezone(timedelta(hours=8)))
    ram_used, ram_total, ram_pct = get_ram_info()
    return {
        'ts': now.isoformat(),
        'model': 'minimax/MiniMax-M3',
        'cpu_pct': round(get_cpu_pct(), 1),
        'ram_used_mb': ram_used,
        'ram_total_mb': ram_total,
        'ram_pct': round(ram_pct, 1),
        'disk_pct': round(get_disk_pct(), 1),
        'openrouter_used': round(get_openrouter_usage(), 4),
        'openrouter_limit': 5.0,
        'brave_count': get_brave_count(),
        'brave_limit': 1000,
    }

# ============================================================
# 2. 抓 portfolio 持股現價
# ============================================================
def yahoo_get_price(code):
    """從 Yahoo Finance 抓現價，失敗回 None"""
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}?interval=1d&range=1d'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        d = json.loads(urllib.request.urlopen(req, timeout=5).read())
        m = d['chart']['result'][0]['meta']
        return m.get('regularMarketPrice', 0)
    except Exception:
        return None

def yahoo_get_usd_twd():
    try:
        url = 'https://query1.finance.yahoo.com/v8/finance/chart/USDTWD=X?interval=1d&range=1d'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        d = json.loads(urllib.request.urlopen(req, timeout=5).read())
        m = d['chart']['result'][0]['meta']
        return m.get('regularMarketPrice', 31.5)
    except Exception:
        return 31.5

def collect_portfolio():
    now = datetime.now(timezone(timedelta(hours=8)))
    usd_twd = yahoo_get_usd_twd()

    stocks = []
    tw_total_cost = 0
    tw_total_market = 0
    us_total_cost = 0
    us_total_market = 0

    for code, code_clean, name, shares, cost in TW_STOCKS:
        price = yahoo_get_price(code) or cost
        cost_total = shares * cost
        market = shares * price
        profit = market - cost_total
        pct = (profit / cost_total * 100) if cost_total else 0
        tw_total_cost += cost_total
        tw_total_market += market
        stocks.append({
            'code': code_clean,
            'name': name,
            'market': 'TW',
            'shares': shares,
            'cost': cost,
            'price': round(price, 2),
            'market_twd': round(market, 0),
            'profit_twd': round(profit, 0),
            'pct': round(pct, 1),
        })

    for code, code_clean, name, shares, cost in US_STOCKS:
        price = yahoo_get_price(code) or cost
        cost_total = shares * cost
        market = shares * price
        profit = market - cost_total
        pct = (profit / cost_total * 100) if cost_total else 0
        us_total_cost += cost_total
        us_total_market += market
        stocks.append({
            'code': code_clean,
            'name': name,
            'market': 'US',
            'shares': shares,
            'cost': round(cost, 2),
            'price': round(price, 2),
            'market_usd': round(market, 0),
            'profit_usd': round(profit, 0),
            'pct': round(pct, 1),
        })

    # 排序
    tw_sorted = sorted([s for s in stocks if s['market'] == 'TW'], key=lambda x: -x['pct'])
    us_sorted = sorted([s for s in stocks if s['market'] == 'US'], key=lambda x: -x['pct'])
    top_gainers = sorted(stocks, key=lambda x: -x['pct'])[:3]
    top_losers = sorted(stocks, key=lambda x: x['pct'])[:1]

    tw_profit = tw_total_market - tw_total_cost
    us_profit = us_total_market - us_total_cost
    total_market_twd = tw_total_market + us_total_market * usd_twd
    total_cost_twd = tw_total_cost + us_total_cost * usd_twd
    total_profit_twd = total_market_twd - total_cost_twd
    total_pct = total_profit_twd / total_cost_twd * 100 if total_cost_twd else 0

    return {
        'ts': now.isoformat(),
        'usd_twd': round(usd_twd, 2),
        'tw_total_market': round(tw_total_market, 0),
        'tw_total_cost': round(tw_total_cost, 0),
        'tw_pct': round(tw_profit / tw_total_cost * 100, 1) if tw_total_cost else 0,
        'us_total_market_usd': round(us_total_market, 0),
        'us_total_cost_usd': round(us_total_cost, 0),
        'us_pct': round(us_profit / us_total_cost * 100, 1) if us_total_cost else 0,
        'total_market_twd': round(total_market_twd, 0),
        'total_cost_twd': round(total_cost_twd, 0),
        'total_profit_twd': round(total_profit_twd, 0),
        'total_pct': round(total_pct, 1),
        'stocks': stocks,
        'top_gainers': top_gainers,
        'top_losers': top_losers,
    }

# ============================================================
# 3. 產生 HTML 預覽（手機看）
# ============================================================
def generate_html_preview(sys_data, portfolio):
    """產生 HTML 預覽，模擬 RLCD-4.2 黑白風格"""
    ts_short = portfolio['ts'][11:16]  # 18:32
    ts_date = portfolio['ts'][:10]    # 2026-06-04
    weekday_map = {'Mon': '一', 'Tue': '二', 'Wed': '三', 'Thu': '四', 'Fri': '五', 'Sat': '六', 'Sun': '日'}
    # 簡化星期
    dt = datetime.fromisoformat(portfolio['ts'])
    weekday_cn = ['一', '二', '三', '四', '五', '六', '日'][dt.weekday()]

    # 頁面載入時的真實時鐘（以 server time 為準，ESP32 實機會用 NTP）
    now_live = datetime.now(timezone(timedelta(hours=8)))
    clock_hms = now_live.strftime('%H:%M:%S')
    clock_date = now_live.strftime('%Y/%m/%d')
    clock_weekday = ['一', '二', '三', '四', '五', '六', '日'][now_live.weekday()]

    # 感測器 placeholder（ESP32 實機會讀 SHTC3 實時數據）
    sensor_temp = 28.3
    sensor_humid = 65

    # 漲跌顏色（黑白版用 ▲▼ 符號，不用色彩）
    def arrow(pct):
        return '▲' if pct >= 0 else '▼'

    def fmt_money(n):
        return f'{n:,.0f}'

    # 漲幅 Top 3 HTML
    gainers_html = ''.join([
        f'<li><span class="code">{escape(s["code"])}</span> <span class="arrow">▲</span> <span class="pct">+{s["pct"]:.1f}%</span></li>'
        for s in portfolio['top_gainers']
    ])

    # 個股列表 HTML
    tw_stocks_html = ''.join([
        f'<tr><td>{escape(s["code"])}</td><td>{s["price"]:.2f}</td><td class="{"up" if s["pct"]>=0 else "down"}">{arrow(s["pct"])} {s["pct"]:+.1f}%</td></tr>'
        for s in portfolio['stocks'] if s['market'] == 'TW'
    ])
    us_stocks_html = ''.join([
        f'<tr><td>{escape(s["code"])}</td><td>${s["price"]:.2f}</td><td class="{"up" if s["pct"]>=0 else "down"}">{arrow(s["pct"])} {s["pct"]:+.1f}%</td></tr>'
        for s in portfolio['stocks'] if s['market'] == 'US'
    ])

    html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>蝦助儀表板預覽</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, "Microsoft JhengHei", "PingFang TC", sans-serif;
    background: #f0f0f0;
    padding: 12px;
    color: #000;
  }}
  .header {{
    display: flex; justify-content: space-between; align-items: center;
    background: #333; color: #fff; padding: 8px 12px;
    border-radius: 6px; margin-bottom: 8px; font-size: 13px;
  }}
  .header a {{ color: #fff; text-decoration: none; font-weight: bold; }}
  .device-row {{ display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; }}
  .device {{
    background: #fff; border: 2px solid #333; border-radius: 8px;
    padding: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.15);
  }}
  .rlcd {{
    width: 400px; max-width: 100%; aspect-ratio: 4 / 3;
    background: #f5f5f0; color: #1a1a1a;
    display: flex; flex-direction: column;
  }}
  .rlcd-title {{
    text-align: center; font-size: 12px; padding: 4px;
    border-bottom: 1px solid #999; font-weight: bold;
  }}
  .rlcd-header {{
    text-align: center; font-size: 12px; padding: 4px;
    border-bottom: 1px solid #ccc; color: #333;
  }}
  .rlcd-clock {{
    text-align: center; font-size: 38px; font-weight: 900;
    font-family: 'Courier New', monospace; padding: 6px;
    border-bottom: 1px solid #ccc;
    letter-spacing: 2px;
  }}
  .rlcd-sensor {{
    text-align: center; font-size: 13px; padding: 4px;
    border-bottom: 1px solid #ccc; color: #222;
  }}
  .rlcd-total {{
    flex: 1; display: flex; flex-direction: column;
    justify-content: center; align-items: center;
    border-bottom: 1px solid #999; padding: 8px;
  }}
  .rlcd-total .label {{ font-size: 12px; color: #555; }}
  .rlcd-total .value {{ font-size: 28px; font-weight: 900; margin: 2px 0; }}
  .rlcd-total .pct {{ font-size: 18px; font-weight: bold; }}
  .rlcd-breakdown {{
    padding: 6px 10px; border-bottom: 1px solid #999; font-size: 12px;
  }}
  .rlcd-breakdown div {{ display: flex; justify-content: space-between; padding: 1px 0; }}
  .rlcd-alerts {{ font-size: 10px; padding: 4px 10px; flex-shrink: 0; text-align: center; }}
  .rlcd-alerts div {{ padding: 1px 0; }}
  .touch {{
    width: 360px; max-width: 100%; aspect-ratio: 1 / 1;
    background: #1a1a2e; color: #fff;
    display: flex; flex-direction: column; padding: 8px;
  }}
  .touch-tabs {{
    display: flex; gap: 4px; padding: 4px; flex-shrink: 0;
  }}
  .touch-tabs .tab {{
    flex: 1; text-align: center; padding: 6px 4px;
    background: #333; border-radius: 4px; font-size: 11px;
    color: #aaa;
  }}
  .touch-tabs .tab.active {{ background: #4a9eff; color: #fff; }}
  .touch-content {{
    flex: 1; padding: 8px 4px; font-size: 11px; overflow: hidden;
  }}
  .touch-content .row {{
    display: flex; justify-content: space-between; padding: 3px 0;
    border-bottom: 1px solid #333;
  }}
  .bar {{
    display: inline-block; height: 8px; background: #4a9eff;
    border-radius: 2px; vertical-align: middle; margin-left: 4px;
  }}
  .up {{ color: #d32f2f; }}
  .down {{ color: #2e7d32; }}
  .rlcd .up, .rlcd .down {{ color: #000; font-weight: bold; }}
  .footer {{
    text-align: center; color: #666; font-size: 11px;
    margin-top: 8px; padding: 4px;
  }}
  @media (max-width: 820px) {{
    .device-row {{ flex-direction: column; align-items: center; }}
  }}
</style>
</head>
<body>

<div class="header">
  <span>🦐 蝦助儀表板預覽</span>
  <span>更新 {ts_short} · {ts_date}({weekday_cn})</span>
  <a href="javascript:location.reload()">🔄 重整</a>
</div>

<div class="device-row">

  <!-- RLCD-4.2 模擬（黑白）-->
  <div class="device rlcd">
    <div class="rlcd-title">RLCD-4.2 預覽（4.2" 黑白 400×300）</div>
    <div class="rlcd-header">{clock_date} ({clock_weekday})　📶 WiFi <span id="wifi">●●●</span></div>
    <div class="rlcd-clock"><span id="clock">{clock_hms}</span></div>
    <div class="rlcd-sensor">🌡️ <span id="temp">{sensor_temp}°C</span>　💧 <span id="humid">{sensor_humid}%</span>　<span style="font-size:9px;color:#888">(ESP32 實機讀 SHTC3)</span></div>
    <div class="rlcd-total">
      <div class="label">總資產</div>
      <div class="value">NT$ {fmt_money(portfolio['total_market_twd'])}</div>
      <div class="pct">+{portfolio['total_pct']:.1f}% ▲</div>
    </div>
    <div class="rlcd-breakdown">
      <div><span>台股</span><span>NT$ {fmt_money(portfolio['tw_total_market'])} <b>+{portfolio['tw_pct']:.1f}%</b></span></div>
      <div><span>美股</span><span>NT$ {fmt_money(portfolio['us_total_market_usd'] * portfolio['usd_twd'])} <b>+{portfolio['us_pct']:.1f}%</b></span></div>
      <div><span>美金</span><span>1 USD = {portfolio['usd_twd']:.2f} TWD</span></div>
    </div>
    <div class="rlcd-alerts">
      <div>🌧️ 6/9 梅雨  🏀 NBA G2 6/6  ⏱ {ts_short}</div>
    </div>
  </div>

  <!-- Touch-LCD-4B 模擬（彩色）-->
  <div class="device touch">
    <div class="touch-tabs">
      <div class="tab">總覽</div>
      <div class="tab active">系統</div>
      <div class="tab">持股</div>
      <div class="tab">個股</div>
    </div>
    <div class="touch-content">
      <div class="row"><span>Model</span><span>{sys_data['model']}</span></div>
      <div class="row"><span>CPU</span><span>{sys_data['cpu_pct']:.1f}%<span class="bar" style="width:{min(sys_data['cpu_pct'],100):.0f}px;background:#4ade80"></span></span></div>
      <div class="row"><span>RAM</span><span>{sys_data['ram_used_mb']}/{sys_data['ram_total_mb']}MB ({sys_data['ram_pct']:.1f}%)<span class="bar" style="width:{min(sys_data['ram_pct'],100):.0f}px;background:#4ade80"></span></span></div>
      <div class="row"><span>Disk</span><span>{sys_data['disk_pct']:.1f}%<span class="bar" style="width:{min(sys_data['disk_pct'],100):.0f}px;background:#fbbf24"></span></span></div>
      <div class="row"><span>OpenRouter</span><span>${sys_data['openrouter_used']:.2f}/${sys_data['openrouter_limit']:.0f}<span class="bar" style="width:{min(sys_data['openrouter_used']/sys_data['openrouter_limit']*100,100):.0f}px;background:#60a5fa"></span></span></div>
      <div class="row"><span>Brave Search</span><span>{sys_data['brave_count']}/{sys_data['brave_limit']}<span class="bar" style="width:{min(sys_data['brave_count']/sys_data['brave_limit']*100,100):.0f}px;background:#fb923c"></span></span></div>
      <div class="row" style="margin-top:6px;color:#4ade80"><span>Gateway ✅</span><span>uptime 正常</span></div>
      <div class="row" style="color:#888"><span>剛剛更新</span><span>{ts_short}</span></div>
    </div>
  </div>

</div>

<div class="footer">
  🟢 Top 3 漲幅：{gainers_html}<br>
  📡 資料來源：Yahoo Finance（每分鐘更新）· VM cron 自動推送
</div>

<script>
// 即時更新時鐘（每 1 秒）
function updateClock() {{
  const d = new Date();
  const hms = d.toTimeString().substring(0, 8);
  const el = document.getElementById("clock");
  if (el) el.textContent = hms;
}}
setInterval(updateClock, 1000);
updateClock();

// 60 秒後自動重整（模擬 ESP32 每分鐘抓 R2）
setTimeout(() => location.reload(), 60000);
</script>
</body>
</html>'''
    return html

# ============================================================
# 4. 上傳 R2
# ============================================================
def upload_to_r2(key, content, content_type='application/json'):
    s3 = boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
    )
    if isinstance(content, str):
        body = content.encode('utf-8')
    else:
        body = content
    s3.put_object(
        Bucket=R2_BUCKET,
        Key=key,
        Body=body,
        ContentType=content_type,
        CacheControl='no-cache',  # 避免邊緣節點 cache
    )
    return f'{R2_PUBLIC_URL}/{key}'

# ============================================================
# Main
# ============================================================
if __name__ == '__main__':
    print('🔄 抓取系統狀態...')
    sys_data = collect_sys()
    print(f'  ✅ CPU: {sys_data["cpu_pct"]}% | RAM: {sys_data["ram_pct"]}% | OR: ${sys_data["openrouter_used"]}')

    print('🔄 抓取持股現價...')
    portfolio = collect_portfolio()
    print(f'  ✅ 總資產: NT$ {portfolio["total_market_twd"]:,.0f} ({portfolio["total_pct"]:+.1f}%)')

    print('🔄 產生 HTML 預覽...')
    html = generate_html_preview(sys_data, portfolio)

    print('🔄 上傳 R2...')
    url_sys = upload_to_r2('dashboard/sys.json', json.dumps(sys_data, ensure_ascii=False, indent=2))
    url_portfolio = upload_to_r2('dashboard/portfolio.json', json.dumps(portfolio, ensure_ascii=False, indent=2))
    url_html = upload_to_r2('dashboard/preview.html', html, content_type='text/html; charset=utf-8')

    print()
    print('=' * 60)
    print('✅ 全部上傳完成！')
    print('=' * 60)
    print(f'📊 系統狀態 JSON: {url_sys}')
    print(f'💰 持股資料 JSON: {url_portfolio}')
    print(f'📱 手機預覽 HTML: {url_html}')
    print()
    print(f'⏰ 更新時間: {portfolio["ts"]}')
