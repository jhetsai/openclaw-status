#!/usr/bin/env python3
"""
合併所有持股+配息資料到單一 JSON
Output: assets/portfolio_data.json
"""
import json, os, datetime, boto3, subprocess, re
from html.parser import HTMLParser

WORKSPACE = '/home/jhe/.openclaw/workspace'
OUT_FILE = os.path.join(WORKSPACE, 'assets', 'portfolio_data.json')
R2_BUCKET = 'shared-files'

# ===== Exchange Rate =====
EXCH_FILE = os.path.join(WORKSPACE, 'exchange_rate.json')
def get_exchange_rate():
    if os.path.exists(EXCH_FILE):
        with open(EXCH_FILE) as f:
            d = json.load(f)
            return {'USD_TWD': float(d.get('USD_TWD', 31.569)),
                    'JPY_TWD': float(d.get('JPY_TWD', 0.204)),
                    'updated': d.get('updated', '')}
    return {'USD_TWD': 31.569, 'JPY_TWD': 0.204, 'updated': ''}

# ===== Taiwan Stocks (current prices + holdings) =====
def load_taiwan_stocks():
    path = os.path.join(WORKSPACE, 'taiwan_stock', 'taiwan_stocks.json')
    with open(path) as f:
        return [s for s in json.load(f) if 'shares' in s and s.get('shares', 0) > 0]

# ===== US Stocks =====
def load_us_stocks():
    path = os.path.join(WORKSPACE, 'us_stock', 'us_stocks.json')
    with open(path) as f:
        return [s for s in json.load(f) if 'shares' in s and s.get('shares', 0) > 0]

# ===== Taiwan Dividends (confirmed + pending from Yahoo) =====
class DivParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.texts = []
    def handle_data(self, data):
        d = data.strip()
        if d:
            self.texts.append(d)

def fetch_tw_dividends(tw_stocks, year_target='2026'):
    """從Yahoo抓取台股配息（指定年份）"""
    shares_map = {s['symbol']: s['shares'] for s in tw_stocks}
    confirmed_rows, pending_rows = [], []
    confirmed_total = pending_total = 0

    for code in shares_map:
        url = f'https://tw.stock.yahoo.com/quote/{code}.TW/dividend'
        try:
            r = subprocess.run(['curl', '-s', '--max-time', '10',
                                '-H', 'User-Agent: Mozilla/5.0', url],
                               capture_output=True, text=True, timeout=12)
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

            cash, dates = None, []
            for t in texts[p_idx+1:]:
                if cash is None and re.match(r'^\d+\.\d+$', t):
                    cash = float(t)
                elif re.match(r'^\d{4}/\d{2}/\d{2}$', t):
                    dates.append(t)
                if len(dates) >= 2:
                    break

            if not (cash and len(dates) >= 2):
                continue

            ex_date, payout_date = dates[0], dates[1]
            payout_yr = payout_date.split('/')[0]
            if payout_yr != str(year_target):
                continue

            sh = shares_map[code]
            amt = sh * cash
            row = {'code': code, 'period': period, 'cash': cash, 'shares': sh,
                   'amount': amt, 'ex_date': ex_date, 'payout': payout_date}

            # 已除息（ex_date <= 今天）-> confirmed
            today = datetime.datetime.now().strftime('%Y/%m/%d')
            if ex_date <= today:
                confirmed_rows.append(row)
                confirmed_total += amt
            else:
                pending_rows.append(row)
                pending_total += amt

    return {
        'confirmed': {'total': confirmed_total, 'rows': confirmed_rows},
        'pending': {'total': pending_total, 'rows': pending_rows}
    }

# ===== Taiwan Historical Dividends by Year (2020-2026) =====
def get_tw_annual_dividends(dividend_data=None):
    """台股歷年配息：從 div_history.json 讀取真實銀行記錄（2020-2026）"""
    hist_path = os.path.join(WORKSPACE, 'taiwan_stock', 'div_history.json')
    with open(hist_path) as f:
        div_hist = json.load(f)
    return [{'year': d['year'], 'amt': d['total']} for d in div_hist['annual']]

    return result

# ===== US Historical Dividends (from static data) =====
def get_us_dividend_annual():
    """美股歷年配息：從 div_history.json 讀取真實銀行記錄（已扣30%預扣，TWD）"""
    hist_path = os.path.join(WORKSPACE, 'us_stock', 'div_history.json')
    with open(hist_path) as f:
        div_hist = json.load(f)
    return [{'year': d['year'], 'total': d['total'],
             'aapl': div_hist['by_stock'].get('AAPL',{}).get('years',{}).get(d['year'],0),
             'msft': div_hist['by_stock'].get('MSFT',{}).get('years',{}).get(d['year'],0),
             'bnd': div_hist['by_stock'].get('BND',{}).get('years',{}).get(d['year'],0)}
            for d in div_hist['annual']]



# ===== Compute derived fields =====
def compute_stock_derived(tw_stocks, us_stocks, fx, tw_div_info=None, us_div_info=None):
    """計算市值、報酬、殖利率等衍生欄位，並從 div_info 填入配息資料"""
    USD_TWD = fx['USD_TWD']
    sector_map = {
        '0056':'高股息/市值型','00692':'公司治理','00712':'不動產REITs',
        '00713':'高股息/品質','00717':'特別股/收益型','00878':'永續/ESG',
        '00891':'半導體/科技','00940':'高股息/市值型','009802':'台股大型股',
        '1101':'水泥/原材料','2886':'金融'
    }

    # 台股
    for s in tw_stocks:
        sym = s.get('symbol', s.get('sym', ''))
        s['mktval'] = s['shares'] * s['price']
        s['totalCost'] = s['shares'] * s['cost']
        s['gain'] = s['mktval'] - s['totalCost']
        s['retPct'] = round(s['gain'] / s['totalCost'] * 100, 1) if s['totalCost'] else 0
        # 殖利率（單次配息 / 成本，均攤到每張1000股）
        info = (tw_div_info or {}).get(sym, {})
        s['div'] = info.get('div', 0)
        s['freq'] = info.get('freq', '-')
        s['sector'] = sector_map.get(sym, '-')
        s['annDiv'] = round(s['shares'] * s['div'], 0)
        s['divYield'] = round(s['div'] / s['price'] * 100, 2) if s['price'] else 0
        s['divYieldCost'] = round(s['div'] / s['cost'] * 100, 2) if s['cost'] else 0

    # 美股
    for s in us_stocks:
        sym = s.get('symbol', s.get('sym', ''))
        info = (us_div_info or {}).get(sym, {})
        s['mktvalTwd'] = round(s['shares'] * s['price'] * USD_TWD)
        s['costTwd'] = round(s['shares'] * s['cost'] * USD_TWD)
        s['gain'] = s['mktvalTwd'] - s['costTwd']
        s['retPct'] = round(s['gain'] / s['costTwd'] * 100, 1) if s['costTwd'] else 0
        s['div'] = info.get('div', 0)
        s['freq'] = info.get('freq', '-')
        s['annDivTwd'] = round(s['shares'] * s['div'] * USD_TWD, 0)
        s['divYield'] = round(s['div'] / s['price'] * 100, 2) if s['price'] else 0
        s['divYieldCost'] = round(s['div'] / s['cost'] * 100, 2) if s['cost'] else 0

    return tw_stocks, us_stocks

# ===== MAIN =====
def main():
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}] Generating portfolio_data.json...")

    # 1. Exchange rate
    fx = get_exchange_rate()

    # 2. Load current stock holdings
    tw_stocks = load_taiwan_stocks()
    us_stocks = load_us_stocks()

    # 3. Use dividend_data.json from R2 (no Yahoo fetch needed)
    import boto3
    with open(os.path.expanduser('~/.api_keys')) as f:
        keys = {k: v for k, v in [l.strip().split('=', 1) for l in f if '=' in l and not l.startswith('#')]}
    s3 = boto3.client('s3', endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
        aws_access_key_id=keys.get('R2_ACCESS_KEY'), aws_secret_access_key=keys.get('R2_SECRET_KEY'))
    try:
        s3.download_file(R2_BUCKET, 'assets/dividend_data.json', '/tmp/dj_annual.json')
        with open('/tmp/dj_annual.json') as f:
            tw_div = json.load(f).get('tw', {})
        print(f"    Using dividend_data.json: confirmed={tw_div.get('confirmed',{}).get('total',0):,.0f}, pending={tw_div.get('pending',{}).get('total',0):,.0f}")
    except Exception as e:
        print(f"    Warning: could not load dividend_data.json: {e}")
        tw_div = {'confirmed':{'total':0,'rows':[]},'pending':{'total':0,'rows':[]}}

    # 4. Taiwan annual history
    tw_annual = get_tw_annual_dividends(tw_div)

    # 5. US annual history
    us_annual = get_us_dividend_annual()

    # 6. Download dividend_data.json from R2 for div_info
    import boto3
    with open(os.path.expanduser('~/.api_keys')) as f:
        keys = {k: v for k, v in [l.strip().split('=', 1) for l in f if '=' in l and not l.startswith('#')]}
    s3 = boto3.client('s3', endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
        aws_access_key_id=keys.get('R2_ACCESS_KEY'), aws_secret_access_key=keys.get('R2_SECRET_KEY'))
    try:
        s3.download_file(R2_BUCKET, 'assets/dividend_data.json', '/tmp/dj_for_div.json')
        with open('/tmp/dj_for_div.json') as f:
            dj = json.load(f)
        tw_div_info = dj.get('tw', {}).get('div_info', {})
        us_div_info = dj.get('us', {}).get('div_info', {})
        print(f"    Loaded div_info from R2: {len(tw_div_info)} TW, {len(us_div_info)} US")
    except Exception as e:
        print(f"    Warning: could not load dividend_data.json: {e}")
        tw_div_info, us_div_info = {}, {}

    # 7. Compute derived
    tw_stocks, us_stocks = compute_stock_derived(tw_stocks, us_stocks, fx, tw_div_info, us_div_info)

    # 8. Build unified JSON
    # Build div_history for stacked chart (per-stock, per-year)
    from pathlib import Path
    colors = ['#00ff88','#00d4ff','#ffd700','#ff6b6b','#c77dff','#ff9500','#7fff00','#ff69b4','#00bfff','#ff4500','#adff2f','#dda0dd']
    us_colors = ['#00d4ff','#00ff88','#ffd700']

    tw_hist_path = Path(WORKSPACE) / 'taiwan_stock' / 'div_history.json'
    us_hist_path = Path(WORKSPACE) / 'us_stock' / 'div_history.json'

    with open(tw_hist_path) as f:
        tw_hist = json.load(f)
    with open(us_hist_path) as f:
        us_hist = json.load(f)

    tw_years = [d['year'] for d in tw_hist['annual']]
    tw_datasets = []
    for i, sym in enumerate(sorted(tw_hist['by_stock'].keys())):
        yr_data = tw_hist['by_stock'][sym]['years']
        data = [round(yr_data.get(yr, 0), 2) for yr in tw_years]
        if any(d > 0 for d in data):
            tw_datasets.append({'label': sym, 'data': data, 'backgroundColor': colors[i % len(colors)]})

    us_years = [d['year'] for d in us_hist['annual']]
    us_datasets = []
    for i, sym in enumerate(['AAPL','MSFT','BND']):
        yr_data = us_hist['by_stock'].get(sym, {}).get('years', {})
        data = [round(yr_data.get(yr, 0), 2) for yr in us_years]
        us_datasets.append({'label': sym, 'data': data, 'backgroundColor': us_colors[i]})

    portfolio = {
        'updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
        'fx': fx,
        'stocks': {
            'tw': tw_stocks,
            'us': us_stocks
        },
        'dividends': {
            'tw': {
                'annual': tw_annual,
                'confirmed': tw_div['confirmed'],
                'pending': tw_div['pending']
            },
            'us': {'annual': us_annual}
        },
        'div_history': {
            'tw': {'years': tw_years, 'datasets': tw_datasets},
            'us': {'years': us_years, 'datasets': us_datasets}
        }
    }

    # 9. Save locally
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w') as f:
        json.dump(portfolio, f, ensure_ascii=False, indent=2)
    print(f"  Saved to {OUT_FILE}")

    # 10. Upload to R2
    print("  Uploading to R2...")
    with open(os.path.expanduser('~/.api_keys')) as f:
        keys = {k: v for k, v in [l.strip().split('=', 1) for l in f if '=' in l and not l.startswith('#')]}
    s3 = boto3.client('s3', endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
        aws_access_key_id=keys.get('R2_ACCESS_KEY'),
        aws_secret_access_key=keys.get('R2_SECRET_KEY'))
    s3.upload_file(OUT_FILE, R2_BUCKET, 'assets/portfolio_data.json',
                   ExtraArgs={'ContentType': 'application/json'})
    print(f"  Uploaded to R2: assets/portfolio_data.json")

if __name__ == '__main__':
    main()