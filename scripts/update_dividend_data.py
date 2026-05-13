#!/usr/bin/env python3
"""
更新 assets/dividend_data.json（台股+美股配息資料）
"""
import json, subprocess, re, datetime, boto3, os
from html.parser import HTMLParser
# Load dynamic exchange rate (臺灣銀行即期匯率本行買入)
WORKSPACE = '/home/jhe/.openclaw/workspace'
_EXCH = os.path.join(WORKSPACE, 'exchange_rate.json')
if os.path.exists(_EXCH):
    try:
        with open(_EXCH) as f:
            _d = json.load(f)
            USD_TWD = float(_d.get('USD_TWD', 31.569))
    except:
        USD_TWD = 31.569
else:
    USD_TWD = 31.569


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
# 每期每股配息（來自 Nasdaq API）
us_shares_now = {'AAPL': 105, 'MSFT': 55, 'BND': 116}
bnd_shares_by_month = {
    '2026-02': 113, '2026-03': 114, '2026-04': 115, '2026-05': 116,
}
confirmed_us, pending_us = [], []
today_str = datetime.datetime.now().strftime('%Y-%m-%d')

for sym, shares in us_shares_now.items():
    try:
        assetclass = 'ETF' if sym == 'BND' else 'STOCKS'
        url = f'https://api.nasdaq.com/api/quote/{sym}/dividends?assetclass={assetclass}&limit=20'
        r = subprocess.run(
            ['curl', '-s', '--max-time', '10', url,
             '-H', 'User-Agent: Mozilla/5.0',
             '-H', 'Accept: application/json',
             '-H', 'Origin: https://www.nasdaq.com',
             '-H', 'Referer: https://www.nasdaq.com/market-activity/' + ('etf' if sym == 'BND' else 'stocks') + '/' + sym.lower() + '/dividend-history'],
            capture_output=True, text=True, timeout=12
        )
        data = json.loads(r.stdout)
        rows = data['data']['dividends']['rows']
        for row_data in rows:
            ex_date = row_data['exOrEffDate']
            payment_date = row_data['paymentDate']
            amount_str = row_data['amount'].replace('$', '').strip()
            per_share = float(amount_str)
            pay_dt = datetime.datetime.strptime(payment_date, '%m/%d/%Y').strftime('%Y-%m-%d')
            # BND 月配需看該筆的月份決定股數
            if sym == 'BND':
                pay_month = pay_dt[:7]
                eff_shares = bnd_shares_by_month.get(pay_month, shares)
            else:
                eff_shares = shares
            gross = round(per_share * eff_shares, 3)
            net = round(gross * 0.7, 3)
            row = {
                'code': sym,
                'date': pay_dt,
                'per_share': per_share,
                'shares': eff_shares,
                'gross': gross,
                'total': net,
                'withheld_30pct': True
            }
            # 只取 2026 年的記錄
            if not pay_dt.startswith('2026'):
                continue
            if pay_dt < today_str:
                confirmed_us.append(row)
            else:
                pending_us.append(row)
    except Exception as e:
        print(f"    {sym} Nasdaq API error: {e}")
    except Exception as e:
        print(f"    {sym} Nasdaq API error: {e}")

conf_usd = sum(r['total'] for r in confirmed_us)
pend_usd = sum(r['total'] for r in pending_us)
print(f"  美股：已除息 {len(confirmed_us)} 筆，${conf_usd:.2f}（~{round(conf_usd*USD_TWD):,.0f} TWD）")
print(f"  美股：待發放 {len(pending_us)} 筆，${pend_usd:.2f}")

# === 美股年化配息資訊（從 Nasdaq API 取 annualizedDividend）===
us_div_info_computed = {}
for sym in us_shares_now.keys():
    try:
        assetclass = 'ETF' if sym == 'BND' else 'STOCKS'
        url = f'https://api.nasdaq.com/api/quote/{sym}/dividends?assetclass={assetclass}&limit=3'
        r2 = subprocess.run(
            ['curl', '-s', '--max-time', '10', url,
             '-H', 'User-Agent: Mozilla/5.0',
             '-H', 'Accept: application/json',
             '-H', 'Origin: https://www.nasdaq.com',
             '-H', 'Referer: https://www.nasdaq.com/market-activity/' + ('etf' if sym == 'BND' else 'stocks') + '/' + sym.lower() + '/dividend-history'],
            capture_output=True, text=True, timeout=12
        )
        data = json.loads(r2.stdout)
        ann_div = float(data['data'].get('annualizedDividend', 0))
        first_row = data['data']['dividends']['rows'][0]
        per_share = float(first_row['amount'].replace('$', ''))
        freq = '月配' if sym == 'BND' else '季配'
        us_div_info_computed[sym] = {
            'div': per_share, 'freq': freq, 'ann_div': ann_div
        }
    except Exception as e:
        print(f"    {sym} div_info error: {e}")

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

# === 台股年化配息資訊（從 confirmed_tw / pending_tw，取最新一筆）===
tw_div_info_computed = {}
all_tw = confirmed_tw + pending_tw
for code in set(r['code'] for r in all_tw):
    rows = [r for r in all_tw if r['code'] == code]
    latest = sorted(rows, key=lambda x: x['payout'], reverse=True)[0]
    cash = latest['cash']  # 每股股利（已是正確單位）
    period = latest['period']
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
        'confirmed': {'total_usd': round(conf_usd, 2), 'total_twd': round(conf_usd * USD_TWD, 0), 'rows': confirmed_us},
        'pending': {'total_usd': round(pend_usd, 2), 'total_twd': round(pend_usd * USD_TWD, 0), 'rows': pending_us},
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
us2026_twd = round((conf_usd + pend_usd) * USD_TWD)

import re
html = re.sub(
    r'\{year:2026,amt:\d+\}',
    f'{{year:2026,amt:{tw2026}}}',
    html
)
us2026_net = round(sum(r['total'] for r in confirmed_us) + sum(r['total'] for r in pending_us), 2)
aapl2026_net = round(sum(r['total'] for r in confirmed_us if r['code']=='AAPL'), 2)
msft2026_net = round(sum(r['total'] for r in confirmed_us if r['code']=='MSFT'), 2)
bnd2026_net = round(sum(r['total'] for r in confirmed_us if r['code']=='BND'), 2)
html = re.sub(
    r'\{year:2026, aapl:[0-9.]+, msft:[0-9.]+, bnd:[0-9.]+, arkk:0, total:[0-9.]+\}',
    f'{{year:2026, aapl:{aapl2026_net}, msft:{msft2026_net}, bnd:{bnd2026_net}, arkk:0, total:{us2026_net}}}',
    html
)

with open('/tmp/index_r2.html', 'w') as f:
    f.write(html)
s3.upload_file('/tmp/index_r2.html', 'shared-files', 'assets/index.html')

print(f'  index.html 2026 年已更新（台股={tw2026:,}，美股={us2026_twd:,} TWD）')

# === 台股配息入帳通知 ===
prev_confirmed_total = 0
try:
    s3.download_file('shared-files', 'assets/dividend_data.json', '/tmp/prev_dividend_data.json')
    with open('/tmp/prev_dividend_data.json') as f:
        prev = json.load(f)
    prev_confirmed_total = prev['tw']['confirmed']['total']
except:
    pass

new_total = sum(r['amount'] for r in confirmed_tw)
if new_total > prev_confirmed_total:
    diff = new_total - prev_confirmed_total
    # 找出新增的 rows
    prev_codes = {r['code'] for r in prev.get('tw', {}).get('confirmed', {}).get('rows', [])}
    new_rows = [r for r in confirmed_tw if r['code'] not in prev_codes]
    if new_rows:
        # 發 Telegram 通知
        with open(os.path.expanduser('~/.api_keys')) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    k, v = line.strip().split('=', 1)
                    if k == 'TELEGRAM_BOT_TOKEN':
                        bot_token = v.strip()
        if bot_token:
            lines = ['📥 台股配息入帳通知']
            for r in new_rows:
                lines.append(f"• {r['code']} {r['payout']} ${r['amount']:,.0f}")
            lines.append(f'━━━━━━━━━━━━━━━━━━')
            lines.append(f'新增合計：${diff:,.0f}')
            text = '\n'.join(lines)
            subprocess.run(
                ['curl', '-s', '-X', 'POST',
                 f'https://api.telegram.org/bot{bot_token}/sendMessage',
                 '-d', 'chat_id=1181571031', '-d', f'text={text}', '-d', 'parse_mode=HTML'],
                capture_output=True
            )
            print(f'  → 已發送台股入帳通知：${diff:,.0f}')

print(f"\n完成：assets/dividend_data.json 已更新")
print(f"  台股合計：{sum(r['amount'] for r in confirmed_tw):,.0f}（已）+ {sum(r['amount'] for r in pending_tw):,.0f}（待）")
print(f"  美股合計：${conf_usd:.2f}（已）+ ${pend_usd:.2f}（待）")