#!/usr/bin/env python3
"""
匯率取得腳本
使用 open.er-api.com（免費，不需要 API Key）
"""

import urllib.request
import json
import sys

def get_exchange_rate(from_currency='USD', to_currency='TWD'):
    """取得匯率"""
    url = f"https://open.er-api.com/v6/latest/{from_currency}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('result') == 'success':
                rate = data['rates'].get(to_currency)
                return rate
    except Exception as e:
        print(f"Error: {e}")
    return None

if __name__ == '__main__':
    # 測試
    rate = get_exchange_rate('USD', 'TWD')
    if rate:
        print(f"USD/TWD: {rate}")
    else:
        print("Failed to get exchange rate")
