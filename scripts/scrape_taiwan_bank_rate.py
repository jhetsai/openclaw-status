#!/usr/bin/env python3
"""
Taiwan Bank (臺灣銀行) exchange rate scraper
Fetches 即期匯率 本行買入 rates for USD and JPY
Updates exchange_rate.json for the asset page
"""
import urllib.request
import json
import re
from datetime import datetime

URL = "https://rate.bot.com.tw/xrt?Lang=zh-TW"

def fetch_rates():
    req = urllib.request.Request(URL, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; Python scraper)'
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8')

    rates = {}

    # USD section: find 美金, then extract 即期 本行買入
    # HTML structure: data-table="本行即期買入" followed by the rate value
    usd_pos = html.find('美金')
    if usd_pos >= 0:
        usd_chunk = html[usd_pos:usd_pos+2000]
        spot_buy = re.search(r'本行即期買入[^<]*<[^>]*>([\d.]+)', usd_chunk)
        if spot_buy:
            rates['USD_TWD'] = float(spot_buy.group(1))

    # JPY section: find 日圓, then extract 即期 本行買入
    jpy_pos = html.find('日圓')
    if jpy_pos >= 0:
        jpy_chunk = html[jpy_pos:jpy_pos+2000]
        spot_buy_jpy = re.search(r'本行即期買入[^<]*<[^>]*>([\d.]+)', jpy_chunk)
        if spot_buy_jpy:
            rates['JPY_TWD'] = float(spot_buy_jpy.group(1))

    return rates

if __name__ == '__main__':
    rates = fetch_rates()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Fallback to last known values if fetch fails
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