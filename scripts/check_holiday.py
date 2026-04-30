#!/usr/bin/env python3
"""檢查今天是否為台股或美股休市日"""
from datetime import date

# 2026 年假日
TW_HOLIDAYS = [
    date(2026, 1, 1),   # 新年元旦
    date(2026, 2, 16),  # 農曆除夕
    date(2026, 2, 17),  # 農曆春節
    date(2026, 2, 18),  # 農曆春節
    date(2026, 2, 19),  # 農曆春節
    date(2026, 2, 20),  # 農曆春節
    date(2026, 2, 27),  # 和平紀念日補假
    date(2026, 4, 3),   # 清明節
    date(2026, 4, 6),   # 兒童節
    date(2026, 5, 1),   # 勞動節
    date(2026, 6, 19),  # 端午節
    date(2026, 9, 25),  # 中秋節
    date(2026, 9, 28),  # 教師節
    date(2026, 10, 9),  # 國慶日
    date(2026, 10, 26), # 光復節
    date(2026, 12, 25), # 行憲紀念日
]

US_HOLIDAYS = [
    date(2026, 1, 1),   # New Year's Day
    date(2026, 1, 19),   # MLK Jr. Day
    date(2026, 2, 16),   # Presidents' Day
    date(2026, 4, 3),    # Good Friday
    date(2026, 5, 25),   # Memorial Day
    date(2026, 6, 19),   # Juneteenth
    date(2026, 7, 3),    # Independence Day (observed)
    date(2026, 9, 7),    # Labor Day
    date(2026, 11, 26),  # Thanksgiving
    date(2026, 12, 25),  # Christmas Day
]

def is_tw_holiday():
    """檢查今天是否為台股休市日"""
    today = date.today()
    return today in TW_HOLIDAYS or today.weekday() >= 5  # 週六週日

def is_us_holiday():
    """檢查今天是否為美股休市日"""
    today = date.today()
    return today in US_HOLIDAYS or today.weekday() >= 5  # 週六週日

if __name__ == '__main__':
    import json
    result = {
        'date': str(date.today()),
        'tw_holiday': is_tw_holiday(),
        'us_holiday': is_us_holiday(),
        'tw_name': '台股休市' if is_tw_holiday() else '台股正常',
        'us_name': '美股休市' if is_us_holiday() else '美股正常',
    }
    print(json.dumps(result, ensure_ascii=False))