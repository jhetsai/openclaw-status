#!/usr/bin/env python3
"""
台股成交量排行 - Yahoo 成交量頁面即時解析 (+ Finance API 漲跌修正)
每30分鐘執行一次，盤中（09:00-13:30）
"""
import urllib.request, re, json, os, time
from datetime import datetime

LOG_DIR   = "/home/jhe/.openclaw/workspace/logs/volume"
PREV_FILE = f"{LOG_DIR}/prev_vol.json"
TOKEN     = "8793435853:AAHF2snG1sYEpno-O0uvvRyPL52cqdxER8A"
CHAT_ID   = "1181571031"

ALERT_VOL_PCT   = 30
ALERT_MIN_VOL   = 3_000_000
ALERT_DROP_PCT  = -5.0
ALERT_RISE_PCT  =  5.0
MAX_ALERTS      = 5

MAX_STOCKS      = 50   # 最多取 50 檔
API_DELAY       = 0.5  # API 間隔（秒），避免 429

try:
    import psycopg2
    PG = {
        'host': '127.0.0.1', 'port': 5432,
        'dbname': 'openclaw', 'user': 'jhe',
        'password': 'openclaw_secure_pass_2026',
    }
    HAS_PG = True
except ImportError:
    HAS_PG = False

# ====== Yahoo Finance API - 取得精確現價和漲跌% ======
def fetch_api_chg(symbol):
    """取 Yahoo Finance API 的現價/前收/漲跌%"""
    time.sleep(API_DELAY)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.TW?interval=1d&range=1d"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        m = data['chart']['result'][0]['meta']
        now  = m['regularMarketPrice']
        prev = m['chartPreviousClose']
        chg  = (now - prev) / prev * 100 if prev else 0.0
        return now, prev, chg
    except Exception as e:
        return None, None, None

# ====== PostgreSQL 寫入 ======
def write_to_pg(stocks, ts):
    if not HAS_PG:
        return
    conn = psycopg2.connect(**PG)
    cur = conn.cursor()
    for s in stocks:
        cur.execute(
            "INSERT INTO stock_volume_snapshots "
            "(snapshot_time, rank, symbol, name, price, chg_pct, volume, amount) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (ts, s['rank'], s['symbol'], s['name'], s['price'],
             s['chg_pct'], s['volume'], s['amount']))
    conn.commit()
    cur.close()
    conn.close()

# ====== Yahoo 成交量頁面解析 ======
def fetch_page_data():
    """從 Yahoo 成交量頁面解析：rank, name, symbol, volume, amount"""
    url = "https://tw.stock.yahoo.com/rank/volume/"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "zh-TW,zh;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        html = r.read().decode("utf-8")

    name_pat = re.compile(
        r'Ell">([^<]{2,20})</div><div class="D\(f\) Ai\(c\)"><span class="Fz\(14px\) C\(#979ba7\) Ell">(\d{4,6})\.TW</span>')
    positions = [(m.start(), m.group(1), m.group(2)) for m in name_pat.finditer(html)]
    span_pat = re.compile(r'<span[^>]*class="[^"]*Jc\(fe[^"]*"[^>]*>([^<]+)</span>')
    all_spans = span_pat.findall(html)

    page_stocks = []
    for i in range(0, min(len(all_spans) - 5, MAX_STOCKS * 6), 6):
        if i // 6 >= len(positions):
            break
        if i // 6 >= MAX_STOCKS:
            break

        _, name, sym = positions[i // 6]
        vs = all_spans[i:i+6]

        try:
            # volume 處理（M/K 格式）
            vol_s = vs[4].replace(',', '').strip()
            if vol_s.endswith('M'):
                vol = float(vol_s[:-1]) * 1_000_000
            elif vol_s.endswith('K'):
                vol = float(vol_s[:-1]) * 1_000
            elif vol_s.endswith('B'):
                vol = float(vol_s[:-1]) * 1_000_000_000
            else:
                vol = float(vol_s)

            amt = float(vs[5].replace(',', ''))

            page_stocks.append({
                'rank':    i // 6 + 1,
                'symbol':  sym,
                'name':    name,
                'volume':  int(vol),
                'amount':  amt,
            })
        except Exception:
            pass

    return page_stocks

# ====== 發 TG ======
def send_tg(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'}
    req  = urllib.request.Request(url, data=json.dumps(data).encode(),
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            print(f"TG OK: {r.status}")
    except Exception as e:
        print(f"TG失敗: {e}")

# ====== 主程式 ======
def main():
    now  = datetime.now()
    t_str = now.strftime('%H:%M')
    print(f"[{t_str}] 成交量排行...")

    # 1. 抓頁面（成交量）
    try:
        page_stocks = fetch_page_data()
    except Exception as e:
        print(f"頁面解析失敗: {e}")
        return

    if not page_stocks:
        print("無資料")
        return

    print(f"頁面取得 {len(page_stocks)} 檔")

    # 2. 每檔取 Yahoo Finance API 取得精確 chg_pct
    print(f"呼叫 API 取得漲跌%（最多 {len(page_stocks)} 檔）...")
    for s in page_stocks:
        now_p, prev, chg = fetch_api_chg(s['symbol'])
        if now_p is not None:
            s['price']    = now_p
            s['prev']     = prev
            s['chg_pct']  = chg
        else:
            s['price']   = 0.0
            s['prev']    = 0.0
            s['chg_pct'] = 0.0

    # 3. 寫入 PG
    ts = now
    try:
        write_to_pg(page_stocks, ts)
    except Exception as e:
        print(f"PG寫入失敗: {e}")

    # 4. 讀上一筆 → Alerts
    prev_map = {}
    if os.path.exists(PREV_FILE):
        with open(PREV_FILE, 'r', encoding='utf-8') as f:
            prev_map = json.load(f)

    alerts = []
    for s in page_stocks:
        sym = s['symbol']
        vol = s['volume']
        pct = s['chg_pct']

        if pct <= ALERT_DROP_PCT:
            alerts.append(f"⚠️ [{sym}] {s['name']} 崩跌 `{pct:.2f}%` $ {s.get('price', '-')}")
        elif pct >= ALERT_RISE_PCT:
            alerts.append(f"📈 [{sym}] {s['name']} 大漲 `+{pct:.2f}%` $ {s.get('price', '-')}")

        if sym in prev_map:
            vol_prev = prev_map[sym]['volume']
            if vol_prev > 0:
                chg = (vol - vol_prev) / vol_prev * 100
                if abs(chg) >= ALERT_VOL_PCT:
                    alerts.append(
                        f"🔥 [{sym}] {s['name']} 成交量 `{'+' if chg > 0 else ''}{chg:.0f}%`\n"
                        f"   {vol_prev//1_000_000:.1f}M → {vol//1_000_000:.1f}M")

        if vol >= ALERT_MIN_VOL:
            alerts.append(f"🚨 [{sym}] {s['name']} 爆量 `{vol//1_000_000:.1f}M` 張")

    # 5. 存上一筆
    with open(PREV_FILE, 'w', encoding='utf-8') as f:
        json.dump({s['symbol']: s for s in page_stocks}, f, ensure_ascii=False)

    # 6. 發 TG
    if alerts:
        msg = f"📊 *成交量警示*  {t_str}\n" + "\n".join(alerts[:MAX_ALERTS])
        if len(alerts) > MAX_ALERTS:
            msg += f"\n_…還有 {len(alerts)-MAX_ALERTS} 檔_"
        send_tg(msg)
        print(f"已發送 {len(alerts)} 則警示")
    else:
        print("無異常")

if __name__ == '__main__':
    main()
