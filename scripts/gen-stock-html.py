#!/usr/bin/env python3
import urllib.request, json, os, subprocess
from datetime import datetime

WORKSPACE = "/home/jhe/.openclaw/workspace"
TW_JSON = os.path.join(WORKSPACE, "taiwan_stock/taiwan_stocks.json")
US_PRICES = os.path.join(WORKSPACE, "us_stock/us_prices.json")
US_STOCKS = os.path.join(WORKSPACE, "us_stock/us_stocks.json")
OUT_HTML = os.path.join(WORKSPACE, "stock", "index.html")
TWSE_DATA_FILE = os.path.join(WORKSPACE, "taiwan_stock/twse_data.json")

with open(TW_JSON) as f:
    tw_stocks = [s for s in json.load(f) if "shares" in s]
with open(US_PRICES) as f:
    us_data = json.load(f)
us_prices = us_data.get("prices", {})
with open(US_STOCKS) as f:
    us_stocks_data = json.load(f)

# Load upcoming ex-dividend dates
upcoming_div = []
if os.path.exists(TWSE_DATA_FILE):
    with open(TWSE_DATA_FILE) as f:
        twse_data = json.load(f)
    from datetime import datetime
    today_roc = f"{datetime.now().year-1911:03d}{datetime.now().month:02d}{datetime.now().day:02d}"
    upcoming_div = [
        d for d in twse_data.get("upcoming_div", [])
        if d.get("Date", "") >= today_roc
    ]
    if upcoming_div:
        # Load manual dividend overrides
        manual_div_file = os.path.join(WORKSPACE, "taiwan_stock/manual_dividend.json")
        manual_div = {}
        if os.path.exists(manual_div_file):
            with open(manual_div_file) as f:
                manual_div = json.load(f)
        div_rows = ""
        for d in upcoming_div[:10]:
            date_tw = d.get("Date", "")
            year = int(date_tw[:3]) + 1911
            month_day = date_tw[3:5] + "/" + date_tw[5:]
            date_str = f"{year}/{month_day}"
            code = d.get("Code", "")
            cash = d.get("CashDividend", "") or ""
            if (cash == "-" or cash == "") and code in manual_div:
                cash = str(manual_div[code]["cash"])
            if not cash or cash == "-":
                cash = "-"
            name = d.get("Name", "")
            # Fetch payout date from Yahoo
            payout_str = "-"
            url = f"https://tw.stock.yahoo.com/quote/{code}.TW/dividend"
            try:
                result = subprocess.run(
                    ['curl', '-s', '--max-time', '8', '-H', 'User-Agent: Mozilla/5.0', url],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    import re
                    html = result.stdout
                    dates = re.findall(r'<div[^>]*>(\d{4}/\d{2}/\d{2})</div>', html)
                    # Convert ROC date_tw (YYYYMMDD format) to AD for comparison (e.g., 1150423 -> 2026/04/23)
                    roc_year = int(date_tw[:3])
                    ad_year = roc_year + 1911
                    month = date_tw[3:5]
                    day = date_tw[5:]
                    date_tw_ad = f"{ad_year}/{month}/{day}"
                    for i in range(0, len(dates)-1, 2):
                        if dates[i] == date_tw_ad:
                            payout_str = dates[i+1]
                            break
            except:
                pass
            div_rows += f"<tr><td>{code}</td><td>{name}</td><td>{date_str}</td><td>{payout_str}</td><td>{cash}</td></tr>\n"
        upcoming_div_html = f"""<div class="card collapsed">
<h3 class="section-title" onclick="this.parentElement.classList.toggle('collapsed')">📅 近期除息預告</h3>
<table>
<tr><th>代碼</th><th>名稱</th><th>除息日</th><th>發放日</th><th>現金股利</th></tr>
{div_rows}</table>
</div>"""
    else:
        upcoming_div_html = ""
else:
    upcoming_div_html = ""

YAHOO_HOSTS = ['query1.finance.yahoo.com', 'query2.finance.yahoo.com']

def fetch_prev_close(symbol):
    for host in YAHOO_HOSTS:
        url = f"https://{host}/v8/finance/chart/{symbol}?interval=1d&range=5d"
        try:
            result = subprocess.run(
                ['curl', '-4', '-s', '--max-time', '8', '-H', 'User-Agent: Mozilla/5.0', url],
                capture_output=True, text=True, timeout=12
            )
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                r = data["chart"]["result"][0]
                closes = [c for c in r["indicators"]["quote"][0]["close"] if c]
                # Use chartPreviousClose only when we don't have enough history (e.g., futures)
                if len(closes) >= 2:
                    return closes[-2]  # actual previous close
                prev = r["meta"].get("chartPreviousClose")
                return prev if prev else closes[-1]
            else:
                continue
        except:
            continue
    return None

USD_TWD = 31.569
FX_COST_RATE = 28.5

# ─── TW ───
tw_total_cost = sum(s.get("total_cost", s["shares"] * s["cost"]) for s in tw_stocks)
tw_total_mv = sum(s.get("market_value", 0) for s in tw_stocks)

tw_day = sum((s.get("price",0) - (s.get("prev_price") or s.get("price",0))) * s["shares"] for s in tw_stocks)

# Mobile 6-col: 代,名,股,現價,漲%,累計
tw_mob = ""
# Desktop 9-col: 代號,名稱,股數,成本均價,昨收,現價,當日,漲%,累計
tw_desk = ""

for s in tw_stocks:
    sym = s["symbol"]; name = s["name"]; shares = s["shares"]
    cost = s.get("cost", 0)
    prev = s.get("prev_price") or s.get("price", 0)
    curr = s.get("price", 0)
    day_val = (curr - prev) * shares
    day_pct = (curr - prev) / prev * 100 if prev else 0
    gain = s.get("gain", 0)
    dc = "up" if day_pct >= 0 else "down"
    gc = "up" if gain >= 0 else "down"
    ds = "+" if day_pct >= 0 else ""
    gs = "+" if gain >= 0 else ""
    gcolor = "#FFD700" if gain >= 0 else "#FF6B6B"

    # Mobile: 代,名,股,現價,漲%,累計
    tw_mob += (
        f"<tr>"
        f"<td>{sym}</td><td>{name}</td><td>{shares:,}</td>"
        f"<td>${curr:.2f}</td>"
        f"<td class='{dc}'>{ds}{day_pct:.2f}%</td>"
        f"<td style='color:{gcolor};font-weight:bold'>{gs}{gain:,.0f}</td>"
        f"</tr>"
    )
    # Desktop: 代號,名稱,股數,成本均價,昨收,現價,當日,漲%,累計
    tw_desk += (
        f"<tr>"
        f"<td>{sym}</td><td>{name}</td><td>{shares:,}</td>"
        f"<td>${cost:.2f}</td><td>${prev:.2f}</td><td>${curr:.2f}</td>"
        f"<td class='{dc}'>{ds}{day_val:,.0f}</td>"
        f"<td class='{dc}'>{ds}{day_pct:.2f}%</td>"
        f"<td style='color:{gcolor};font-weight:bold'>{gs}{gain:,.0f}</td>"
        f"</tr>"
    )

# ─── US ───
us_info = [("AAPL","蘋果",105,145.02),("MSFT","微軟",55,263.51),("BND","債ETF",116,73.2156)]
us_cost_twd = 0; us_mv_twd = 0; us_day_twd = 0; us_cost_twd_285 = 0; us_mv_usd = 0
us_mob = ""; us_desk = ""

SYMBOL_ALIAS = {"^FNMR": "FNMR", "WTX&": "WTX", "WTXP&": "WTXP", "IX0126.TW": "TX"}
for sym, name, shares, cost in us_info:
    alias = SYMBOL_ALIAS.get(sym, sym.lstrip('^'))
    price = us_prices.get(sym, us_prices.get(alias, us_prices.get(sym.split('.')[0], 0)))
    prev = us_data.get('prev', {}).get(sym) or next((s['prev'] for s in us_stocks_data if s['symbol'] == sym), price)
    day_val_usd = (price - prev) * shares
    day_pct = (price - prev) / prev * 100 if prev else 0
    mv_usd = price * shares; cost_tot_usd = cost * shares
    gain_twd = (mv_usd - cost_tot_usd) * USD_TWD
    day_twd = day_val_usd * USD_TWD
    dc = "up" if day_pct >= 0 else "down"
    gc = "up" if gain_twd >= 0 else "down"
    ds = "+" if day_pct >= 0 else ""
    gs = "+" if gain_twd >= 0 else ""
    gcolor = "#FFD700" if gain_twd >= 0 else "#FF6B6B"

    us_mob += (
        f"<tr>"
        f"<td>{sym}</td><td>{name}</td><td>{shares}</td>"
        f"<td>${price:.2f}</td>"
        f"<td class='{dc}'>{ds}{day_pct:.2f}%</td>"
        f"<td style='color:{gcolor};font-weight:bold'>{gs}{gain_twd:,.0f}</td>"
        f"</tr>"
    )
    us_desk += (
        f"<tr>"
        f"<td>{sym}</td><td>{name}</td><td>{shares}</td>"
        f"<td>${cost:.2f}</td><td>${prev:.2f}</td><td>${price:.2f}</td>"
        f"<td class='{dc}'>{ds}{day_twd:,.0f}</td>"
        f"<td class='{dc}'>{ds}{day_pct:.2f}%</td>"
        f"<td style='color:{gcolor};font-weight:bold'>{gs}{gain_twd:,.0f}</td>"
        f"</tr>"
    )
    us_cost_twd += cost_tot_usd * USD_TWD
    us_mv_twd += mv_usd * USD_TWD
    us_cost_twd_285 += cost_tot_usd * FX_COST_RATE
    us_mv_usd += mv_usd
    us_day_twd += day_twd

# ─── Reference Futures/Indices ───
ref_info = [
    ("^TWII", "台灣加權指數", 0, 0),
    ("WTX&", "台指期(近一)", 0, 0),
    ("SPY", "S&P 500", 0, 0),
    ("QQQ", "Nasdaq 100", 0, 0),
    ("DIA", "道瓊", 0, 0),
    ("VIXY", "VIX恐慌指數", 0, 0),
    ("TLT", "10年公債殖利率", 0, 0),
    ("GLD", "黃金", 0, 0),
    ("USO", "原油", 0, 0),
    ("^FNMR", "NAREIT Mortgage", 0, 0),
]
REF_SYMBOL_ALIAS = {
    "^FNMR": "^FNMR", "WTX&": "WTX", "WTXP&": "WTXP",
    "^TWII": "TAIEX",
    "SPY": "SPY", "QQQ": "QQQ", "DIA": "DIA",
    "VIXY": "VIXY", "TLT": "TLT",
    "GLD": "GLD", "USO": "USO"
}
# Map Finnhub ETF symbol to us_prev/us_prices key
REF_CODE_MAP = {
    "^FNMR": "FNMR",
    "SPY": "SP500", "QQQ": "NAS100", "DIA": "DOW",
    "VIXY": "VIX", "TLT": "TNX", "GLD": "GOLD", "USO": "OIL"
}
ref_mob = ""; ref_desk = ""

for sym, name, shares, cost in ref_info:
    alias = REF_SYMBOL_ALIAS.get(sym, sym.lstrip('^').split('.')[0])
    price = us_prices.get(REF_CODE_MAP.get(alias, alias), 0)
    prev = us_data.get('prev', {}).get(REF_CODE_MAP.get(alias, alias)) or next((s['prev'] for s in us_stocks_data if s['symbol'] == sym), price)
    day_pct = (price - prev) / prev * 100 if prev else 0
    dc = "up" if day_pct >= 0 else "down"
    ds = "+" if day_pct >= 0 else ""
    # Mobile: 4 columns
    ref_mob += (
        f"<tr>"
        f"<td>{sym}</td><td>{name}</td>"
        f"<td>{price:.2f}</td>"
        f"<td class='{dc}'>{ds}{day_pct:.2f}%</td>"
        f"</tr>"
    )
    # Desktop: 5 columns
    ref_desk += (
        f"<tr>"
        f"<td>{sym}</td><td>{name}</td>"
        f"<td>{prev:.2f}</td><td>{price:.2f}</td>"
        f"<td class='{dc}'>{ds}{day_pct:.2f}%</td>"
        f"</tr>"
    )

# ─── Totals ───
total_mv = tw_total_mv + us_mv_twd
total_cost = tw_total_cost + us_cost_twd
total_gain = total_mv - total_cost
us_fx_gain = (USD_TWD - FX_COST_RATE) * us_mv_usd
total_with_fx = total_gain + us_fx_gain
total_pct = total_gain / total_cost * 100
total_day = tw_day + us_day_twd
now_str = datetime.now().strftime("%Y/%m/%d %H:%M")
gain_color = "#FFD700" if total_gain >= 0 else "#FF6B6B"
gain_sign = "+" if total_gain >= 0 else ""
total_with_fx_sign = "+" if total_with_fx >= 0 else ""
day_color = "#FFD700" if total_day >= 0 else "#FF6B6B"
tw_day_color = "#FFD700" if tw_day >= 0 else "#FF6B6B"
tw_day_sign = "+" if tw_day >= 0 else ""
day_sign = "+" if total_day >= 0 else ""
us_day_color = "#FFD700" if us_day_twd >= 0 else "#FF6B6B"
us_day_sign = "+" if us_day_twd >= 0 else ""

# Mobile headers
HDR6 = "<th>代</th><th>名</th><th>股</th><th>現價</th><th>漲%</th><th>累計</th>"
# Desktop headers
HDR9 = "<th>代號</th><th>名稱</th><th>股數</th><th>成本均價</th><th>昨收</th><th>現價</th><th>當日</th><th>漲%</th><th>累計</th>"
COL6 = "<col style='width:12%'><col style='width:18%'><col style='width:10%'><col style='width:14%'><col style='width:12%'><col style='width:34%'>"
COL9 = "<col style='width:8%'><col style='width:13%'><col style='width:7%'><col style='width:10%'><col style='width:10%'><col style='width:10%'><col style='width:9%'><col style='width:7%'><col style='width:26%'>"

STYLE = """
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',Arial,sans-serif;background:#f0f2f5;min-height:100vh;padding:10px}
.header{text-align:center;margin-bottom:16px}
.header h1{color:#1a1a2e;font-size:20px;margin-bottom:4px}
.header p{color:#666;font-size:12px}
.card{background:white;border-radius:12px;padding:12px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.1)}
.kpi-row{display:flex;gap:10px;justify-content:center;margin:12px 0;flex-wrap:wrap}
.kpi-box{flex:0 0 auto;background:#2196F3;color:white;padding:10px 14px;border-radius:10px;text-align:center;min-width:100px}
.kpi-box .label{font-size:10px;opacity:0.9}
.kpi-box .value{font-size:19px;font-weight:bold;margin:4px 0}
.kpi-box .sub{font-size:9px;opacity:0.85}
.kpi-box.orange{background:#E65100}
.kpi-box.green{background:#2E7D32}
.section-title{color:#333;font-size:14px;font-weight:bold;margin-bottom:10px;padding-bottom:6px;border-bottom:2px solid #2196F3;cursor:pointer;user-select:none;display:block}
.section-title:hover{opacity:0.8}
.section-title::after{content:' ▼';font-size:10px;color:#888}
.card.collapsed>table,.card.collapsed>div.kpi-row,.card.collapsed>p{display:none}
.card.collapsed>.section-title{border-bottom:none;margin-bottom:0;padding-bottom:4px}
.card.collapsed>.section-title::after{content:' ▶';font-size:10px;color:#888}
.mob-table{display:table}
.desk-table{display:none}
table{width:100%;border-collapse:collapse;font-size:11px;table-layout:auto}
th,td{padding:5px 3px;text-align:center;border-bottom:1px solid #eee;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
th{background:#1a1a2e;color:white;font-size:9px}
.up{color:#4CAF50;font-weight:bold}
.down{color:#F44336;font-weight:bold}
.footer{text-align:center;color:#999;font-size:10px;margin-top:16px}
@media(min-width:768px){
body{padding:20px}
.header{margin-bottom:24px}
.header h1{font-size:24px}
.header p{font-size:13px}
.card{padding:20px;margin-bottom:16px}
.kpi-row{gap:80px;margin:15px 0}
.kpi-box{padding:14px 22px;min-width:145px}
.kpi-box .label{font-size:12px}
.kpi-box .value{font-size:26px}
.kpi-box .sub{font-size:11px}
.section-title{font-size:15px;margin-bottom:12px;padding-bottom:8px}
.mob-table{display:none}
.desk-table{display:table}
table{font-size:12px}
th,td{padding:9px 7px}
.footer{font-size:11px;margin-top:20px}
}
</style>"""

HTML = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>持股總覽｜蝦助</title>
{STYLE}
</head>
<body>
<div class="header">
<h1>📊 持股總覽</h1>
<p>最後更新：{now_str} | USD/TWD：{USD_TWD}</p>
</div>
<div class="card">
<div class="kpi-row">
<div class="kpi-box">
<div class="label">總市值</div>
<div class="value">{total_mv:,.0f}</div>
<div class="sub">TWD</div>
</div>
<div class="kpi-box">
<div class="label">總成本</div>
<div class="value">{total_cost:,.0f}</div>
<div class="sub">TWD</div>
</div>
<div class="kpi-box orange">
<div class="label">累計報酬</div>
<div class="value" style="color:{gain_color}">{gain_sign}{total_gain:,.0f}</div>
<div class="sub" style="color:{gain_color}">{gain_sign}{total_pct:.1f}%</div>
</div>
<div class="kpi-box" style="background:#1565C0">
<div class="label">台股當日</div>
<div class="value" style="color:{tw_day_color}">{tw_day_sign}{tw_day:,.0f}</div>
<div class="sub" style="color:{tw_day_color}">TWD</div>
</div>
<div class="kpi-box" style="background:#E65100">
<div class="label">美股當日</div>
<div class="value" style="color:{us_day_color}">{us_day_sign}{us_day_twd:,.0f}</div>
<div class="sub" style="color:{us_day_color}">TWD</div>
</div>
</div>
</div>
<div class="card collapsed">
<h3 class="section-title" onclick="this.parentElement.classList.toggle('collapsed')">📈 台股（{len(tw_stocks)} 檔）</h3>
<table class="mob-table">

<tr>{HDR6}</tr>
{tw_mob}
</table>
<table class="desk-table">

<tr>{HDR9}</tr>
{tw_desk}
</table>
</div>
<div class="card collapsed">
<h3 class="section-title" onclick="this.parentElement.classList.toggle('collapsed')">💵 美股（3 檔）</h3>
<table class="mob-table">

<tr>{HDR6}</tr>
{us_mob}
</table>
<table class="desk-table">

<tr>{HDR9}</tr>
{us_desk}
</table>
</div>
<div class="card collapsed">
<h3 class="section-title" onclick="this.parentElement.classList.toggle('collapsed')">📊 期貨 / 指數參考</h3>
<table class="mob-table">
<tr><th>代</th><th>名</th><th>價格</th><th>漲%</th></tr>
{ref_mob}
</table>
<table class="desk-table">
<tr><th>代號</th><th>名稱</th><th>昨收</th><th>現價</th><th>漲%</th></tr>
{ref_desk}
</table>
</div>
<div class="card collapsed">
<h3 class="section-title" onclick="this.parentElement.classList.toggle('collapsed')">💰 2026年配息總覽</h3>
<table>
<tr><th>項目</th><th>金額</th><th>說明</th></tr>
<tr><td>台股已入帳</td><td style="color:#4CAF50;font-weight:bold">+53,221 元</td><td>1~4月對帳單</td></tr>
<tr><td>台股待發放</td><td style="color:#FF9800;font-weight:bold">+7,251 元</td><td>5月（0056、00717、00940）</td></tr>
<tr><td>美股實收</td><td style="color:#4CAF50;font-weight:bold">+USD 111.87</td><td>≈ TWD 3,573（已扣30%預扣稅）</td></tr>
<tr style="background:#f5f5f5;font-weight:bold"><td>合計實收</td><td style="color:#2e7d32">≈ 56,794 元</td><td>台股+美股</td></tr>
<tr style="background:#fff9e6"><td>總累計</td><td style="color:#FFD700;font-weight:bold">{total_with_fx_sign}{total_with_fx:,.0f} 元</td><td>市值增值+美股匯差（成本匯率 28.5）</td></tr>
</table>
</div>
{upcoming_div_html}
<div class="footer">📊 持股總覽｜蝦助出品｜{now_str}</div>
</body>
</html>"""

with open(OUT_HTML, "w") as f:
    f.write(HTML)
print(f"OK: {len(HTML)} bytes")
print(f"當日: {day_sign}{total_day:,.0f} | 累計: {gain_sign}{total_gain:,.0f}")

# ===== R2 Upload =====
import boto3, os
try:
    with open(os.path.expanduser("~/.api_keys")) as f:
        for line in f:
            if line.strip() and not line.startswith("#") and "=" in line:
                k, v = line.strip().split("=", 1)
                os.environ[k.strip()] = v.strip()
except:
    pass

s3 = boto3.client('s3', endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
    aws_access_key_id=os.environ.get('R2_ACCESS_KEY'),
    aws_secret_access_key=os.environ.get('R2_SECRET_KEY'))
with open(OUT_HTML, 'rb') as f:
    s3.put_object(Bucket='shared-files', Key='stock/index.html', Body=f.read(), ContentType='text/html')
print("R2 stock/index.html uploaded")
