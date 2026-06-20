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
    """台股歷年配息：
    - 2020-2025: 從 taiwan_stock/div_history.json 讀取（歷史資料）
    - 2026: 從 dividend_data.json 讀取（confirmed + pending）
    """
    # 讀取歷史資料（2020-2025）
    hist_path = os.path.join(WORKSPACE, 'taiwan_stock', 'div_history.json')
    with open(hist_path) as f:
        div_hist = json.load(f)
    
    result = []
    for d in div_hist['annual']:
        year = d['year']
        if year == '2026':
            continue  # 2026 單獨處理
        result.append({'year': year, 'amt': d['total']})
    
    # 2026 年：從 dividend_data.json 讀取（confirmed + pending）
    div_path = os.path.join(WORKSPACE, 'assets', 'dividend_data.json')
    with open(div_path) as f:
        div_data = json.load(f)
    
    tw_conf = div_data.get('tw', {}).get('confirmed', {}).get('total', 0)
    tw_pend = div_data.get('tw', {}).get('pending', {}).get('total', 0)
    result.append({'year': '2026', 'amt': tw_conf + tw_pend})
    
    return result

    return result

# ===== US Historical Dividends (from static data) =====
def get_us_dividend_annual(fx_rate=31.569):
    """美股歷年配息：
    - 2020-2025: 從 div_history.json 讀取（歷史 TWD 資料）
    - 2026: 從 dividend_data.json 讀取（confirmed + pending），轉換為 TWD
    """
    # 讀取歷史資料（2020-2025）
    hist_path = os.path.join(WORKSPACE, 'us_stock', 'div_history.json')
    with open(hist_path) as f:
        div_hist = json.load(f)
    
    result = []
    for d in div_hist['annual']:
        year = d['year']
        if year == '2026':
            continue  # 2026 單獨處理
        result.append({
            'year': year,
            'total': d['total'],
            'currency': 'TWD',
            'original_currency': 'TWD'
        })
    
    # 2026 年：從 dividend_data.json 讀取（confirmed + pending）
    div_path = os.path.join(WORKSPACE, 'assets', 'dividend_data.json')
    with open(div_path) as f:
        div_data = json.load(f)
    
    us_conf = div_data.get('us', {}).get('confirmed', {})
    us_pend = div_data.get('us', {}).get('pending', {})
    
    usd_total = 0
    for r in us_conf.get('rows', []):
        usd_total += r.get('total', 0)
    for r in us_pend.get('rows', []):
        usd_total += r.get('total', 0)
    
    twd_2026 = round(usd_total * fx_rate, 2)
    result.append({
        'year': '2026',
        'total': twd_2026,
        'currency': 'TWD',
        'original_currency': 'USD'
    })
    
    return result



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

    # 2b. Fill prev_price from us_prices.json (correct source, not us_stocks.json)
    US_PRICES_FILE = os.path.join(WORKSPACE, 'us_stock', 'us_prices.json')
    if os.path.exists(US_PRICES_FILE):
        with open(US_PRICES_FILE) as f:
            us_price_data = json.load(f)
        us_prev_map = us_price_data.get('prev', {})  # {'AAPL': 292.68, 'MSFT': 412.66, ...}
        print(f"    US prev from us_prices.json: {us_prev_map}")
        for s in us_stocks:
            sym = s.get('symbol', '')
            s['prev_price'] = us_prev_map.get(sym, s.get('price'))
    else:
        print("    Warning: us_prices.json not found, using fallback prev")
        for s in us_stocks:
            s['prev_price'] = s.get('prev', s.get('price'))

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
    us_annual = get_us_dividend_annual(fx['USD_TWD'])

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
    # 取得匯率用於 2026 USD -> TWD 轉換
    usd_to_twd = fx['USD_TWD']
    for i, sym in enumerate(['AAPL','MSFT','BND']):
        yr_data = us_hist['by_stock'].get(sym, {}).get('years', {})
        # 檢查 2026 是否為 USD（根據 currency_note 或新版結構）
        data = []
        for yr in us_years:
            val = yr_data.get(yr, 0)
            # 如果是 2026 年且值很小（約 < 1000），很可能是 USD
            if yr == '2026' and isinstance(val, (int, float)) and val < 1000:
                val = round(val * usd_to_twd, 2)  # USD -> TWD 轉換
            elif isinstance(val, dict):
                # 新結構：{'amt': xx, 'currency': 'USD/TWD'}
                currency = val.get('currency', 'TWD')
                if currency == 'USD':
                    val = round(val['amt'] * usd_to_twd, 2)
                else:
                    val = val['amt']
            data.append(round(val, 2))
        us_datasets.append({'label': sym, 'data': data, 'backgroundColor': us_colors[i]})

    # Pre-compute summary fields (stock-only, no cash)
    ORIG_USD_RATE = 28.4481
    US_BASE_COST = 105*145.02 + 116*73.21 + 55*263.51
    usCostAtBase = US_BASE_COST * ORIG_USD_RATE
    twCost = sum(s['totalCost'] for s in tw_stocks)
    stockCost = twCost + usCostAtBase
    twMktval = sum(s['mktval'] for s in tw_stocks)
    usMktval = sum(s.get('mktvalTwd', 0) for s in us_stocks)
    stockMktval = twMktval + usMktval
    # 台股 2026 已入帳+待發放（實際數字）
    tw_confirmed = tw_div.get('confirmed', {}).get('total', 0)
    tw_pending = tw_div.get('pending', {}).get('total', 0)
    tw_annual_2026 = tw_confirmed + tw_pending
    
    # 美股 2026 實際配息（從 div_history.json，取已轉換的 TWD 值）
    us_div_2026_twd = 0
    for entry in us_annual:
        if entry.get('year') == '2026':
            us_div_2026_twd = entry.get('total', 0)
            break
    
    annualDiv = round(tw_annual_2026 + us_div_2026_twd)
    yieldCost = f"{(annualDiv / stockCost * 100):.2f}%" if stockCost > 0 else "0%"
    yieldCur = f"{(annualDiv / stockMktval * 100):.2f}%" if stockMktval > 0 else "0%"

    # 載入現有 portfolio_data.json，保留 usd_cash 和 jpy_cash
    existing_cash = {'usd_cash': None, 'jpy_cash': None}
    if os.path.exists(OUT_FILE):
        try:
            with open(OUT_FILE, 'r') as f:
                existing = json.load(f)
                existing_cash['usd_cash'] = existing.get('usd_cash')
                existing_cash['jpy_cash'] = existing.get('jpy_cash')
        except:
            pass

    portfolio = {
        'updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
        'fx': fx,
        'usd_cash': existing_cash['usd_cash'] if existing_cash['usd_cash'] else {'cash_usd': 0, 'total_invested_usd': 0, 'invested_for美股_usd': 0, 'original_rate': 28.4481},
        'jpy_cash': existing_cash['jpy_cash'] if existing_cash['jpy_cash'] else {'cash_jpy': 0, 'total_invested_jpy': 0, 'withdrawn_jpy': 0, 'original_rate': 0.2365},
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
        },
        'summary': {
            'stockCost': round(stockCost),
            'stockMktval': round(stockMktval),
            'annualDiv': round(annualDiv),
            'yieldCost': yieldCost,
            'yieldCur': yieldCur
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