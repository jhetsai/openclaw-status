#!/usr/bin/env python3
"""Update gen-stock-html.py to add payout date column to dividend table"""
import subprocess, re, os

WORKSPACE = "/home/jhe/.openclaw/workspace"
GEN_HTML = os.path.join(WORKSPACE, "scripts/gen-stock-html.py")

# Read the file
content = open(GEN_HTML).read()

# First, let's add the fetch_dividend_info function after the imports
fetch_func = '''
def fetch_dividend_info(code):
    """Fetch next dividend ex-date and payout date from Yahoo Finance Taiwan"""
    url = f"https://tw.stock.yahoo.com/quote/{code}.TW/dividend"
    try:
        result = subprocess.run(
            ['curl', '-s', '--max-time', '10', '-H', 'User-Agent: Mozilla/5.0', url],
            capture_output=True, text=True, timeout=12
        )
        if result.returncode != 0:
            return None, None
        html = result.stdout
        pattern = r'<div[^>]*>(\\d{4}/\\d{2}/\\d{2})</div>'
        all_dates = re.findall(pattern, html)
        # Pairs: (除息日, 發放日)
        for i in range(0, len(all_dates) - 1, 2):
            ex = all_dates[i]
            payout = all_dates[i+1] if i+1 < len(all_dates) else None
            return ex, payout
        return None, None
    except:
        return None, None

'''

# Insert the function after the imports (before the first function definition)
# Find the position after "from datetime import datetime" line
import_insert_pos = content.find('from datetime import datetime')
if import_insert_pos > 0:
    # Find end of that line
    line_end = content.find('\n', import_insert_pos)
    if line_end > 0:
        content = content[:line_end+1] + fetch_func + content[line_end+1:]

# Now modify the upcoming_div table to include 發放日 column
old_table_header = '<tr><th>代碼</th><th>名稱</th><th>除息日</th><th>現金股利</th></tr>'
new_table_header = '<tr><th>代碼</th><th>名稱</th><th>除息日</th><th>發放日</th><th>現金股利</th></tr>'
content = content.replace(old_table_header, new_table_header)

# Modify the row generation to include payout date and fetch from Yahoo
# Find and replace the div_rows generation
old_row = '''div_rows += f"<tr><td>{code}</td><td>{name}</td><td>{date_str}</td><td>{cash}</td></tr>\\n"'''
new_row = '''# Fetch payout date from Yahoo
            payout_str = "-"
            ex_yahoo, payout_yahoo = fetch_dividend_info(code)
            if payout_yahoo:
                payout_str = payout_yahoo
            div_rows += f"<tr><td>{code}</td><td>{name}</td><td>{date_str}</td><td>{payout_str}</td><td>{cash}</td></tr>\\n"'
content = content.replace(old_row, new_row)

# Save
open(GEN_HTML, 'w').write(content)
print('Done')