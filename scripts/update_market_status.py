from datetime import datetime as dt
import json
from datetime import datetime as dt
import sys
from datetime import datetime as dt
import os
from datetime import date

# 2026 年假日
TW_HOLIDAYS = [
    date(2026, 1, 1), date(2026, 2, 16), date(2026, 2, 17), date(2026, 2, 18),
    date(2026, 2, 19), date(2026, 2, 20), date(2026, 2, 27), date(2026, 4, 3),
    date(2026, 4, 6), date(2026, 5, 1), date(2026, 6, 19), date(2026, 9, 25),
    date(2026, 9, 28), date(2026, 10, 9), date(2026, 10, 26), date(2026, 12, 25),
]
US_HOLIDAYS = [
    date(2026, 1, 1), date(2026, 1, 19), date(2026, 2, 16), date(2026, 4, 3),
    date(2026, 5, 25), date(2026, 6, 19), date(2026, 7, 3), date(2026, 9, 7),
    date(2026, 11, 26), date(2026, 12, 25),
]

def is_tw_holiday():
    today = date.today()
    return today in TW_HOLIDAYS or today.weekday() >= 5

def is_us_holiday():
    today = date.today()
    return today in US_HOLIDAYS or today.weekday() >= 5

now_str = dt.now().strftime('%Y-%m-%d %H:%M:%S')
result = {
    'date': now_str,
    'tw': {'status': '休市中' if is_tw_holiday() else '交易中', 'holiday': is_tw_holiday()},
    'us': {'status': '休市中' if is_us_holiday() else '交易中', 'holiday': is_us_holiday()}
}

os.makedirs('/home/jhe/.openclaw/workspace/stock', exist_ok=True)
with open('/home/jhe/.openclaw/workspace/stock/market_status.json', 'w') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"TW={result['tw']['status']}, US={result['us']['status']}")