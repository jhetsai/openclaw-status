#!/usr/bin/env python3
"""Fix fetch-stock-prices.py: fetch_taiwan_futures -> fetch_taiwan_page"""
import re

with open('/home/jhe/.openclaw/workspace/scripts/fetch-stock-prices.py', 'r') as f:
    content = f.read()

# Fix 1: replace function definition
old = 'def fetch_taiwan_futures(symbol):\n    """Fetch Taiwan futures (WTX&, WTXP&) from Yahoo Taiwan page"""\n    url = f"https://tw.stock.yahoo.com/future/{symbol}"'
new = 'def fetch_taiwan_page(symbol):\n    """Fetch price + prev from Yahoo Taiwan page (all ref indices)"""\n    url = f"https://tw.stock.yahoo.com/quote/{symbol}"'
content = content.replace(old, new)

# Fix 2: replace inner content (import re + regex)
old2 = '            import re\n            html = result.stdout\n            m = re.search(r\'"price"\\s*:\\s*\\{\\s*"raw"\\s*:\\s*"?([0-9.]+)\', html)\n            if m:\n                return float(m.group(1))\n        return None'
new2 = '            html = result.stdout\n            m_price = re.search(r\'"price"\\s*:\\s*\\{\\s*"raw"\\s*:\\s*"?([0-9.]+)\', html)\n            price = float(m_price.group(1)) if m_price else None\n            m_prev = re.search(r\'"previousClose"\\s*:\\s*"?([0-9.]+)\', html)\n            prev = float(m_prev.group(1)) if m_prev else None\n            if price:\n                return price, prev\n        return None, None'
content = content.replace(old2, new2)

# Fix 3: replace WTX special handling with generic ref_only logic
old3 = '''    # WTX& and WTXP& need special handling via Taiwan page
    if sym in ("WTX&", "WTXP&"):
        p = fetch_taiwan_futures(sym)
        if p:
            us_prices[code] = p
            print(f"  {code}: {p} (Taiwan futures)")
        else:
            print(f"  {code}: failed")
    else:'''
new3 = '''    if item.get("ref_only"):
        price, prev = fetch_taiwan_page(sym)
        if price:
            us_prices[code] = price
            if prev:
                us_prev[code] = prev
            print(f"  {code}: {price} / {prev} (Taiwan Yahoo ref)")
        else:
            print(f"  {code}: failed")
    else:'''
content = content.replace(old3, new3)

with open('/home/jhe/.openclaw/workspace/scripts/fetch-stock-prices.py', 'w') as f:
    f.write(content)

# Verify
with open('/home/jhe/.openclaw/workspace/scripts/fetch-stock-prices.py', 'r') as f:
    verify = f.read()

errors = []
if 'def fetch_taiwan_page' in verify:
    print('✓ fetch_taiwan_page exists')
else:
    errors.append('✗ fetch_taiwan_page NOT found')

if 'def fetch_taiwan_futures' not in verify:
    print('✓ fetch_taiwan_futures removed')
else:
    errors.append('✗ fetch_taiwan_futures still present')

if 'ref_only' in verify:
    print('✓ ref_only logic present')
else:
    errors.append('✗ ref_only logic missing')

if errors:
    print('ERRORS:', errors)
else:
    print('All checks passed!')