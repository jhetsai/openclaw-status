#!/usr/bin/env python3
"""
add_finnhub_fallback.py - 加 Finnhub 備援到 fetch-stock-prices.py
"""

import re

# Read the current file
with open('/home/jhe/.openclaw/workspace/scripts/fetch-stock-prices.py', 'r') as f:
    content = f.read()

# 1. Add FINNHUB_API_KEY to the key loading section (after the existing key loading)
if 'FINNHUB_API_KEY' not in content:
    # Find a good place to add the Finnhub key loading
    key_load = '''# Load API keys
KEYS = {}
key_file = os.path.join(WORKSPACE, ".api_keys")
if os.path.exists(key_file):
    with open(key_file) as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                KEYS[k] = v'''
    
    # Insert after the first import block
    content = content.replace(
        'import json, urllib.request, urllib.error, os, subprocess',
        'import json, urllib.request, urllib.error, os, subprocess\n\nKEYS = {}\nkey_file = os.path.join(WORKSPACE, ".api_keys")\nif os.path.exists(key_file):\n    with open(key_file) as f:\n        for line in f:\n            if "=" in line:\n                k, v = line.strip().split("=", 1)\n                KEYS[k] = v\nFINNHUB_KEY = KEYS.get("FINNHUB_API_KEY", "")'
    )

# 2. Add Finnhub fetch function before the US stocks fetching section
finnhub_func = '''
def fetch_finnhub_price(symbol):
    """Fetch US stock price from Finnhub (fallback)"""
    if not FINNHUB_KEY:
        return None
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_KEY}"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("c") and data["c"] > 0:
                return data["c"]
    except Exception:
        pass
    return None

'''

# Insert before "Fetching US stocks from Yahoo"
content = content.replace(
    'print("Fetching US stocks from Yahoo...")',
    finnhub_func + 'print("Fetching US stocks from Yahoo...")'
)

# 3. Update the US stocks fetching to add Finnhub fallback
# Find the pattern where we fetch yahoo price and add fallback
old_code = '''        p = fetch_yahoo_price(sym)
        if p:
            us_prices[code] = p
            print("  " + code + ": " + str(p))'''

new_code = '''        p = fetch_yahoo_price(sym)
        if p:
            us_prices[code] = p
            print("  " + code + ": " + str(p))
        else:
            # Finnhub fallback
            p2 = fetch_finnhub_price(sym)
            if p2:
                us_prices[code] = p2
                print(f"  {code}: {p2} (Finnhub fallback)")'''

content = content.replace(old_code, new_code)

# Write back
with open('/home/jhe/.openclaw/workspace/scripts/fetch-stock-prices.py', 'w') as f:
    f.write(content)

print("✅ 已加入 Finnhub 備援機制")
