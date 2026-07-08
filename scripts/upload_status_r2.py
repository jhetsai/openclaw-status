#!/usr/bin/env python3
"""upload_status_r2.py — 上傳 status_esp32.json 到 R2"""
import boto3, os, sys

KEYS_FILE = os.path.expanduser('~/.api_keys')
KEYS = {}
if os.path.exists(KEYS_FILE):
    for line in open(KEYS_FILE):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            KEYS[k.strip()] = v.strip()

R2_KEY    = KEYS.get('R2_ACCESS_KEY', '')
R2_SECRET = KEYS.get('R2_SECRET_KEY', '')
SRC_FILE  = '/home/jhe/.openclaw/workspace/assets/status_esp32.json'

if not os.path.exists(SRC_FILE):
    print("status_esp32.json not found, skipping")
    sys.exit(0)

try:
    s3 = boto3.client('s3',
        endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
        aws_access_key_id=R2_KEY,
        aws_secret_access_key=R2_SECRET)
    s3.upload_file(SRC_FILE, 'shared-files', 'assets/status_esp32.json',
                    ExtraArgs={'ContentType': 'application/json', 'ACL': 'public-read'})
    print(f"[upload_status_r2] uploaded {SRC_FILE} → R2 assets/status_esp32.json")
except Exception as e:
    print(f"[upload_status_r2] ERROR: {e}")
