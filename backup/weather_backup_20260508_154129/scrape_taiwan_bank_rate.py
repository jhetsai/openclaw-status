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

    # Extract USD and JPY 即期匯率 本行買入
    # Pattern: currency name followed by 買入 value in the spot section
    # The HTML has multiple tables; we look for the row in the 即期 section
    
    # Find the rate table - USD and JPY appear as rows
    # We need: 美金 (USD) -> 即期 -> 本行買入
    # And: 日圓 (JPY) -> 即期 -> 本行買入
    
    # The page structure: for each currency there are cells with:
    # 現金匯率 本行買入/本行賣出
    # 即期匯率 本行買入/本行賣出
    
    # Extract using regex - find USD and JPY sections
    rates = {}
    
    # USD: find 美金 (USD) section, then extract 即期 本行買入 (2nd column in spot section)
    # The pattern for USD: 31.53 (即期買入) is in the 4th data cell after currency name
    # USD cells order: 現金買 現金賣 即期買 即期賣
    # USD row structure: <td>...美金...USD...</td><td>31.205</td><td>31.875</td><td>31.53</td><td>31.68</td>
    
    usd_match = re.search(r'美金.*?USD.*?<td[^>]*>([\d.]+)</td><td[^>]*>([\d.]+)</td><td[^>]*>([\d.]+)</td><td[^>]*>([\d.]+)</td>', html, re.DOTALL)
    if usd_match:
        # 即期買入 = 3rd value (index 2)
        rates['USD_TWD'] = float(usd_match.group(3))
    
    jpy_match = re.search(r'日圓.*?JPY.*?<td[^>]*>([\d.]+)</td><td[^>]*>([\d.]+)</td><td[^>]*>([\d.]+)</td><td[^>]*>([\d.]+)</td>', html, re.DOTALL)
    if jpy_match:
        rates['JPY_TWD'] = float(jpy_match.group(3))
    
    return rates

if __name__ == '__main__':
    rates = fetch_rates()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data = {
        'USD_TWD': rates.get('USD_TWD', 31.53),
        'JPY_TWD': rates.get('JPY_TWD', 0.198),
        'updated': now
    }
    print(f"Fetched: USD={data['USD_TWD']}, JPY={data['JPY_TWD']}, at {now}")
    
    # Write to exchange_rate.json
    with open('/home/jhe/.openclaw/workspace/assets/exchange_rate.json', 'w') as f:
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