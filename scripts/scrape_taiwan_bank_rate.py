#!/usr/bin/env python3
"""
Exchange rate scraper via Yahoo Finance
Fetches USD/TWD and JPY/TWD rates in real-time
Updates exchange_rate.json for the asset page
"""
import urllib.request
import json
from datetime import datetime

def fetch_rates():
    # Yahoo Finance currency pairs
    usd_twd_url = 'https://query1.finance.yahoo.com/v8/finance/chart/USDTWD=X?interval=1d&range=1d'
    jpy_twd_url = 'https://query1.finance.yahoo.com/v8/finance/chart/JPYTWD=X?interval=1d&range=1d'

    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        req1 = urllib.request.Request(usd_twd_url, headers=headers)
        with urllib.request.urlopen(req1, timeout=10) as resp:
            data1 = json.loads(resp.read())
        usd_twd = data1['chart']['result'][0]['meta']['regularMarketPrice']
    except Exception as e:
        print(f'USD/TWD fetch failed: {e}')
        usd_twd = None

    try:
        req2 = urllib.request.Request(jpy_twd_url, headers=headers)
        with urllib.request.urlopen(req2, timeout=10) as resp:
            data2 = json.loads(resp.read())
        jpy_twd = data2['chart']['result'][0]['meta']['regularMarketPrice']
    except Exception as e:
        print(f'JPY/TWD fetch failed: {e}')
        jpy_twd = None

    return {
        'USD_TWD': round(usd_twd, 4) if usd_twd else None,
        'JPY_TWD': round(jpy_twd, 4) if jpy_twd else None
    }

if __name__ == '__main__':
    rates = fetch_rates()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    data = {
        'USD_TWD': rates.get('USD_TWD', 31.375),
        'JPY_TWD': rates.get('JPY_TWD', 0.1984),
        'updated': now
    }
    print(f"Fetched: USD={data['USD_TWD']}, JPY={data['JPY_TWD']}, at {now}")

    # Write to BOTH locations so all scripts read the same file
    # 1. assets/ (for R2 static hosting)
    with open('/home/jhe/.openclaw/workspace/assets/exchange_rate.json', 'w') as f:
        json.dump(data, f, indent=2)

    # 2. workspace root (for gen_portfolio_data.py and other scripts)
    with open('/home/jhe/.openclaw/workspace/exchange_rate.json', 'w') as f:
        json.dump(data, f, indent=2)

    # Upload to R2
    import boto3
    client = boto3.client(
        's3',
        endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
        aws_access_key_id='fbe5ece2074eaa2b7829b6986b1cc499',
        aws_secret_access_key='de99b120611ba90bd5662a4517cb21e60d544ab1c3a015c0cbbbd6e8afa6b5fe',
        region_name='auto'
    )
    client.upload_file('/home/jhe/.openclaw/workspace/assets/exchange_rate.json', 'shared-files', 'exchange_rate.json',
        ExtraArgs={'ContentType': 'application/json'})
    print("Uploaded to R2")
