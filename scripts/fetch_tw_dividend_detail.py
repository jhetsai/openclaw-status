#!/usr/bin/env python3
"""Debug version of fetch_tw_dividend_detail.py"""
import subprocess, re, json, os, sys
from datetime import datetime

WORKSPACE = "/home/jhe/.openclaw/workspace"
OUT_FILE = os.path.join(WORKSPACE, "taiwan_stock/tw_dividend_detail.json")

HOLDINGS = [
    "0056", "00692", "00712", "00713", "00717",
    "00878", "00891", "00940", "009802", "1101", "2886"
]

def fetch_yahoo_dividend(code):
    url = f"https://tw.stock.yahoo.com/quote/{code}.TW/dividend"
    print(f"[DEBUG] START code={code}", file=sys.stderr, flush=True)
    try:
        result = subprocess.run(
            ['curl', '-s', '--max-time', '10', '-H', 'User-Agent: Mozilla/5.0', url],
            capture_output=True, text=True, timeout=12
        )
        print(f"[DEBUG] rc={result.returncode} len={len(result.stdout)}", file=sys.stderr, flush=True)
        if result.returncode != 0:
            print(f"[DEBUG] returning []: non-zero rc", file=sys.stderr, flush=True)
            return []
        html = result.stdout
        cells = re.findall(r'<div[^>]*>([^<]*)</div>', html)
        print(f"[DEBUG] cells={len(cells)}", file=sys.stderr, flush=True)
        PERIOD_PAT = re.compile(r'^\d{4}(Q[1-4]|H[1-2]|M\d{1,2})$')
        DATE_PAT = re.compile(r'^\d{4}/\d{2}/\d{2}$')
        results = []
        start_idx = None
        for i in range(25, min(len(cells), 50)):
            if PERIOD_PAT.match(cells[i].strip()):
                start_idx = i
                print(f"[DEBUG] period at i={i}: {cells[i]!r}", file=sys.stderr, flush=True)
                break
        if start_idx is None:
            print(f"[DEBUG] returning []: no period found", file=sys.stderr, flush=True)
            return []
        print(f"[DEBUG] start_idx={start_idx}", file=sys.stderr, flush=True)
        i = start_idx
        while i + 4 < len(cells):
            period = cells[i].strip()
            cash_div = cells[i+1].strip()
            ex_date = cells[i+2].strip()
            payout_date = cells[i+4].strip()
            print(f"[DEBUG] i={i}: p={period!r} ex={ex_date!r} cash={cash_div!r}", file=sys.stderr, flush=True)
            if not PERIOD_PAT.match(period):
                print(f"[DEBUG] break: period no match", file=sys.stderr, flush=True)
                break
            if not DATE_PAT.match(ex_date):
                print(f"[DEBUG] skip: ex_date no match", file=sys.stderr, flush=True)
                i += 6
                continue
            try:
                cash_val = float(cash_div)
            except:
                print(f"[DEBUG] skip: bad cash", file=sys.stderr, flush=True)
                i += 6
                continue
            year = int(ex_date.split('/')[0])
            if year < 2024:
                print(f"[DEBUG] skip: year<2024", file=sys.stderr, flush=True)
                i += 6
                continue
            results.append({
                "code": code,
                "period": period,
                "cash_dividend": cash_val,
                "ex_date": ex_date,
                "payout_date": payout_date if payout_date not in ('-', '', None) else None
            })
            print(f"[DEBUG] appended: {results[-1]}", file=sys.stderr, flush=True)
            i += 6
        print(f"[DEBUG] returning results={results}", file=sys.stderr, flush=True)
        return results
    except Exception as e:
        import traceback
        print(f"[DEBUG] EXCEPTION: {e}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        print(f"[DEBUG] returning [] due to exception", file=sys.stderr, flush=True)
        return []

print(f"Fetching Taiwan dividend details for {len(HOLDINGS)} stocks...", flush=True)
all_data = {}
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

for code in HOLDINGS:
    print(f"  Fetching {code}...", end=" ", flush=True)
    rows = fetch_yahoo_dividend(code)
    print(f"  rows={rows!r}", file=sys.stderr, flush=True)
    if rows:
        all_data[code] = rows
        print(f"OK ({len(rows)} records)")
    else:
        print(f"No data")

output = {"updated": now, "stocks": all_data}
with open(OUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
total = sum(len(v) for v in all_data.values())
print(f"\nDone. Saved {total} records → {OUT_FILE}")