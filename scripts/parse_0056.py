import subprocess, re

url = "https://tw.stock.yahoo.com/quote/0056.TW/dividend"
result = subprocess.run(
    ['curl', '-s', '--max-time', '10', '-H', 'User-Agent: Mozilla/5.0', url],
    capture_output=True, text=True, timeout=12
)
html = result.stdout

# Find all dates in YYYY/MM/DD format from div elements
pattern = r'<div[^>]*>(\d{4}/\d{2}/\d{2})</div>'
all_dates = re.findall(pattern, html)

print(f"Total dates found: {len(all_dates)}")
print(f"First 15 dates: {all_dates[:15]}")
print()

# First date should be 除息日 (ex-date), second is 發放日 (payout date)
print("Pairs (除息日 → 發放日):")
for i in range(0, len(all_dates) - 1, 2):
    if i+1 < len(all_dates):
        ex = all_dates[i]
        payout = all_dates[i+1]
        # 除息日 should be before or equal to 發放日 (usually within same year or next)
        print(f"  {ex} → {payout}")