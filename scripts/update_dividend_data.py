#!/usr/bin/env python3
"""
更新 assets/dividend_data.json（台股+美股配息資料）
"""
import json, subprocess, re, datetime, boto3, os
from html.parser import HTMLParser

class DivParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.texts = []
    def handle_data(self, data):
        d = data.strip()
        if d:
            self.texts.append(d)

print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}] 開始更新配息資料...")

# === 台股 ===
TW_JSON = "/home/jhe/.openclaw/workspace/taiwan_stock/taiwan_stocks.json"
with open(TW_JSON) as f:
    tw_stocks = [s for s in json.load(f) if "shares" in s]
shares_map_tw = {s['symbol']: s['shares'] for s in tw_stocks}
today = datetime.datetime.now().strftime('%Y/%m/%d')

confirmed_tw, pending_tw = [], []
for code in shares_map_tw:
    url = f'https://tw.stock.yahoo.com/quote/{code}.TW/dividend'
    try:
        r = subprocess.run(['curl', '-s', '--max-time', '10', '-H', 'User-Agent: Mozilla/5.0', url], capture_output=True, text=True, timeout=12)
        html = r.stdout
    except:
        continue
    for m in re.finditer(r'>(\d{4}Q[1-4])</div>|>(\d{4}M\d{1,2})</div>', html):
        period = m.group(1) or m.group(2)
        start = m.start()
        chunk = html[start:start+1500]
        p = DivParser()
        p.feed(chunk)
        texts = p.texts
        if texts and texts[0].startswith('>'):
            texts[0] = texts[0][1:]
        try:
            p_idx = texts.index(period)
        except ValueError:
            continue
        cash = None
        dates = []
        for t in texts[p_idx+1:]:
            if cash is None and re.match(r'^\d+\.\d+$', t):
                cash = float(t)
            elif re.match(r'^\d{4}/\d{2}/\d{2}$', t):
                dates.append(t)
        if not (cash and len(dates) >= 2):
            continue
        ex_date, payout_date = dates[0], dates[1]
        if payout_date.split('/')[0] != '2026':
            continue
        sh = shares_map_tw[code]
        row = {'code': code, 'period': period, 'cash': cash, 'shares': sh, 'amount': round(sh * cash), 'ex_date': ex_date, 'payout': payout_date}
        if payout_date < today:
            confirmed_tw.append(row)
        else:
            pending_tw.append(row)

print(f"  台股：已入帳 {len(confirmed_tw)} 筆，{sum(r['amount'] for r in confirmed_tw):,.0f} 元")
print(f"  台股：待發放 {len(pending_tw)} 筆，{sum(r['amount'] for r in pending_tw):,.0f} 元")

# === 美股 ===
us_shares_now = {'AAPL': 105, 'MSFT': 55, 'BND': 116}
bnd_historical_shares = {
    '2026-02-02': 113,
    '2026-03-02': 114,
    '2026-04-01': 115,
    '2026-05-01': 116,
}
# 年化配息率（每股股利 x 頻率）
us_div_info = {
    'AAPL': {'div': 1.030, 'freq': '季配', 'per_year': 4},
    'MSFT': {'div': 3.400, 'freq': '季配', 'per_year': 4},
    'BND':  {'div': 3.091, 'freq': '月配', 'per_year': 12},
}
confirmed_us, pending_us = [], []
today_ts = int(datetime.datetime.now().timestamp())

for sym, shares in us_shares_now.items():
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=1y&interval=1d&events=div'
    r = subprocess.run(['curl', '-s', '--max-time', '10', '-H', 'User-Agent: Mozilla/5.0', url], capture_output=True, text=True, timeout=12)
    try:
        data = json.loads(r.stdout)
        result = data['chart']['result'][0]
        events = result.get('events', {})
        if 'dividends' in events:
            for date_str, info in events['dividends'].items():
                ts = int(date_str)
                dt = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                if not dt.startswith('2026'):
                    continue
                amt = info.get('amount', 0)
                effective_shares = bnd_historical_shares.get(dt, shares)
                gross = round(amt * effective_shares, 3)
                net = round(gross * 0.7, 3)
                row = {'code': sym, 'date': dt, 'per_share': amt, 'shares': effective_shares, 'gross': gross, 'total': net, 'withheld_30pct': True}
                if ts < today_ts:
                    confirmed_us.append(row)
                else:
                    pending_us.append(row)
    except:
        pass

conf_usd = sum(r['total'] for r in confirmed_us)
pend_usd = sum(r['total'] for r in pending_us)
print(f"  美股：已入帳 {len(confirmed_us)} 筆，${conf_usd:.2f}（~{round(conf_usd*31.569):,.0f} TWD）")
print(f"  美股：待發放 {len(pending_us)} 筆，${pend_usd:.2f}")

# === 美股年化配息資訊（寫入 div_info）===
us_div_info_computed = {}
for sym, info in us_div_info.items():
    ann = round(info['div'] * info['per_year'], 3)
    us_div_info_computed[sym] = {'div': info['div'], 'freq': info['freq'], 'ann_div': ann}

# === 歷年股息收入（美股）===
us_annual = [
    {'year':2020, 'aapl':0, 'msft':37.18, 'bnd':0, 'total':37.18},
    {'year':2021, 'aapl':781.32, 'msft':1434.74, 'bnd':0, 'total':2216.06},
    {'year':2022, 'aapl':1919.91, 'msft':2862.23, 'bnd':607.42, 'total':5389.56},
    {'year':2023, 'aapl':2199.68, 'msft':3383.95, 'bnd':4806.72, 'total':10390.35},
    {'year':2024, 'aapl':2291.99, 'msft':3735.23, 'bnd':5766.68, 'total':11793.90},
    {'year':2025, 'aapl':2384.93, 'msft':4123.69, 'bnd':7224.73, 'total':13733.34},
]
# 2026年美股實收（從 confirmed_us 計算）
us2026 = {'aapl':0, 'msft':0, 'bnd':0, 'total':0}
for r in confirmed_us:
    key = r['code'].lower()
    if key in us2026:
        us2026[key] += r['gross']
us2026['total'] = sum(us2026.values())
us_annual.append({'year':2026, **us2026})

# === 台股歷年股息收入 ===
tw_annual = [
    {'year':2020,'amt':4190},
    {'year':2021,'amt':66708},
    {'year':2022,'amt':94486},
    {'year':2023,'amt':117027},
    {'year':2024,'amt':183829},
    {'year':2025,'amt':200917},
]

# === 合併 ===
# === 台股歷年股息收入（從 confirmed_tw 累計2026年）===
tw2026_amt = sum(r['amount'] for r in confirmed_tw if r['payout'].startswith('2026'))
tw_annual.append({'year': 2026, 'amt': tw2026_amt})

# === 台股年化配息資訊（從 tw_dividend_detail.json）===
tw_div_info_computed = {}
try:
    with open('/home/jhe/.openclaw/workspace/taiwan_stock/tw_dividend_detail.json') as f:
        twdd = json.load(f)
    for code, records in twdd.get('stocks', {}).items():
        # 取最新一筆（已除息的最近期）
        latest = sorted(records, key=lambda x: x['payout_date'], reverse=True)[0] if records else None
        if latest:
            period = latest['period']
            cash = latest['cash_dividend']
            # 推估頻率
            if 'Q' in period:
                freq = '季配'
                per_year = 4
            elif 'H' in period:
                freq = '半年配'
                per_year = 2
            elif 'M' in period:
                freq = '月配'
                per_year = 12
            else:
                freq = '年配'
                per_year = 1
            ann = round(cash * per_year, 3)
            tw_div_info_computed[code] = {'div': cash, 'freq': freq, 'ann_div': ann}
except:
    pass

# === 合併所有資料 ===
div_data = {
    'updated': today,
    'tw': {
        'confirmed': {'total': sum(r['amount'] for r in confirmed_tw), 'rows': sorted(confirmed_tw, key=lambda x: x['payout'])},
        'pending': {'total': sum(r['amount'] for r in pending_tw), 'rows': sorted(pending_tw, key=lambda x: x['payout'])},
        'annual': tw_annual,
        'div_info': tw_div_info_computed,
    },
    'us': {
        'confirmed': {'total_usd': round(conf_usd, 2), 'total_twd': round(conf_usd * 31.569, 0), 'rows': confirmed_us},
        'pending': {'total_usd': round(pend_usd, 2), 'total_twd': round(pend_usd * 31.569, 0), 'rows': pending_us},
        'annual': us_annual,
        'div_info': us_div_info_computed,
    }
}

# === 上傳 R2 ===
with open(os.path.expanduser("~/.api_keys")) as f:
    for line in f:
        if line.strip() and not line.startswith("#") and "=" in line:
            k, v = line.strip().split("=", 1)
            os.environ[k.strip()] = v.strip()

s3 = boto3.client('s3',
    endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
    aws_access_key_id=os.environ.get('R2_ACCESS_KEY'),
    aws_secret_access_key=os.environ.get('R2_SECRET_KEY'))

with open('/tmp/dividend_data.json', 'w') as f:
    json.dump(div_data, f, ensure_ascii=False, indent=2)
s3.upload_file('/tmp/dividend_data.json', 'shared-files', 'assets/dividend_data.json')

# === 更新 index.html 中的 2026 年動態數值（燒進靜態檔）===
s3.download_file('shared-files', 'assets/index.html', '/tmp/index_r2.html')
with open('/tmp/index_r2.html') as f:
    html = f.read()

tw2026 = sum(r['amount'] for r in confirmed_tw) + sum(r['amount'] for r in pending_tw)
us2026_twd = round((conf_usd + pend_usd) * 31.569)

import re
html = re.sub(
    r'\{year:2026,amt:\d+\}',
    f'{{year:2026,amt:{tw2026}}}',
    html
)
aapl2026 = round(sum(r['gross'] for r in confirmed_us if r['code']=='AAPL'))
msft2026 = round(sum(r['gross'] for r in confirmed_us if r['code']=='MSFT'))
bnd2026 = round(sum(r['gross'] for r in confirmed_us if r['code']=='BND'))
html = re.sub(
    r'\{year:2026, aapl:[\d.]+, msft:[\d.]+, bnd:[\d.]+, total:[\d.]+\}',
    f'{{year:2026, aapl:{aapl2026}, msft:{msft2026}, bnd:{bnd2026}, total:{us2026_twd}}}',
    html
)

with open('/tmp/index_r2.html', 'w') as f:
    f.write(html)
s3.upload_file('/tmp/index_r2.html', 'shared-files', 'assets/index.html')

print(f'  index.html 2026 年已更新（台股={tw2026:,}，美股={us2026_twd:,} TWD）')

print(f"\n完成：assets/dividend_data.json 已更新")
print(f"  台股合計：{sum(r['amount'] for r in confirmed_tw):,.0f}（已）+ {sum(r['amount'] for r in pending_tw):,.0f}（待）")
print(f"  美股合計：${conf_usd:.2f}（已）+ ${pend_usd:.2f}（待）")