#!/usr/bin/env python3
"""
美股配息 Cron：每天 09:00 自動執行
1. pending → confirmed（發放日已過）
2. 發 Telegram 通知
"""
import os, json, boto3
from datetime import datetime
import subprocess

WORKSPACE = '/home/jhe/.openclaw/workspace'
R2_BUCKET = 'shared-files'
TELEGRAM_BOT_TOKEN = None
TELEGRAM_CHAT_ID = '1181571031'

def load_keys():
    with open(os.path.expanduser('~/.api_keys')) as f:
        return {k: v for k, v in [l.strip().split('=', 1) for l in f if '=' in l and not l.startswith('#')]}

def download(keys):
    s3 = boto3.client('s3', endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
        aws_access_key_id=keys.get('R2_ACCESS_KEY'), aws_secret_access_key=keys.get('R2_SECRET_KEY'))
    s3.download_file(R2_BUCKET, 'assets/dividend_data.json', '/tmp/cron_div.json')
    with open('/tmp/cron_div.json') as f:
        return json.load(f)

def upload(keys, dj):
    s3 = boto3.client('s3', endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
        aws_access_key_id=keys.get('R2_ACCESS_KEY'), aws_secret_access_key=keys.get('R2_SECRET_KEY'))
    with open('/tmp/cron_div.json', 'w') as f:
        json.dump(dj, f, indent=2, ensure_ascii=False)
    s3.upload_file('/tmp/cron_div.json', R2_BUCKET, 'assets/dividend_data.json')

def send_telegram(token, chat_id, text):
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    subprocess.run(
        ['curl', '-s', '-X', 'POST', url,
         '-d', f'chat_id={chat_id}', '-d', f'text={text}', '-d', 'parse_mode=HTML'],
        capture_output=True
    )

def main():
    today = datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f'[{today}] US Dividend Cron 開始')

    keys = load_keys()
    token = keys.get('TELEGRAM_BOT_TOKEN')

    dj = download(keys)
    us_pending = dj['us']['pending']['rows']
    us_confirmed = dj['us']['confirmed']['rows']

    moved = []
    remaining = []

    for row in us_pending:
        if datetime.strptime(row['date'], '%Y-%m-%d') <= datetime.now():
            moved.append(row)
        else:
            remaining.append(row)

    if not moved:
        print('  → 無待入帳項目，結束')
        return

    # Update pending
    dj['us']['pending']['rows'] = remaining
    dj['us']['pending']['total_usd'] = round(sum(r['total'] for r in remaining), 2)
    dj['us']['pending']['total_twd'] = round(dj['us']['pending']['total_usd'] * 31.569, 2)

    # Update confirmed
    for row in moved:
        dj['us']['confirmed']['rows'].append(row)
        dj['us']['confirmed']['total_usd'] = round(dj['us']['confirmed']['total_usd'] + row['total'], 2)
        dj['us']['confirmed']['total_twd'] = round(dj['us']['confirmed']['total_twd'] + row['total'] * 31.569, 2)

    upload(keys, dj)

    # Compose Telegram message
    lines = ['📥 <b>美股配息入帳通知</b>\n']
    for r in moved:
        lines.append(f'• {r["code"]} {r["date"]} 實收 ${r["total"]}')
    text = '\n'.join(lines)

    if token:
        send_telegram(token, TELEGRAM_CHAT_ID, text)
        print(f'  → 已發送 Telegram 通知')
    else:
        print('  → 無 BOT_TOKEN，略過通知')

    print(f'  → 已移至 confirmed: {[r["code"]+" "+r["date"] for r in moved]}')

    # Log
    log = os.path.join(WORKSPACE, 'logs', 'us_dividend_cron.log')
    with open(log, 'a') as f:
        f.write(f'[{today}] 移至 confirmed: {moved}\n')

if __name__ == '__main__':
    main()