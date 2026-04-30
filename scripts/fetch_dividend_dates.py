#!/usr/bin/env python3
"""Fetch dividend ex-date and payout dates from Yahoo Finance Taiwan"""
import subprocess, re, sys, json
from datetime import datetime

def fetch_dividend_dates(symbol):
    """Fetch dividend ex-date and payout dates from Yahoo Finance Taiwan"""
    url = f"https://tw.stock.yahoo.com/quote/{symbol}.TW/dividend"
    result = subprocess.run(
        ['curl', '-s', '--max-time', '10', '-H', 'User-Agent: Mozilla/5.0', url],
        capture_output=True, text=True, timeout=12
    )
    if result.returncode != 0:
        return []
    
    html = result.stdout
    
    # Find all dates in YYYY/MM/DD format from div elements
    pattern = r'<div[^>]*>(\d{4}/\d{2}/\d{2})</div>'
    all_dates = re.findall(pattern, html)
    
    # Dates appear in pairs: (除息日, 發放日)
    results = []
    for i in range(0, len(all_dates) - 1, 2):
        if i+1 < len(all_dates):
            ex_date = all_dates[i]
            payout_date = all_dates[i+1]
            if ex_date > '2000/01/01' and payout_date > '2000/01/01':
                results.append({"ex_date": ex_date, "payout_date": payout_date})
    
    return results[:8]

if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "0056"
    results = fetch_dividend_dates(symbol)
    print(f"{symbol} 除息日 → 發放日:")
    for r in results:
        print(f"  {r['ex_date']} → {r['payout_date']}")