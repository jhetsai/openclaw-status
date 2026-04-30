#!/usr/bin/env python3
import boto3

ACCESS_KEY = 'R2_ACCESS_KEY_REDACTED'
SECRET_KEY = 'R2_SECRET_KEY_REDACTED'
ENDPOINT = 'https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com'
BUCKET = 'shared-files'

s3 = boto3.client(
    's3',
    endpoint_url=ENDPOINT,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
)

files = [
    ('dashboard/index.html', '/home/jhe/.openclaw/workspace/dashboard/index.html'),
    ('dashboard/index-CBMFbfwO.js', '/home/jhe/.openclaw/workspace/dashboard/index-CBMFbfwO.js'),
    ('dashboard/index-nqMpL4T3.css', '/home/jhe/.openclaw/workspace/dashboard/index-nqMpL4T3.css'),
]

for r2_key, local_path in files:
    try:
        s3.upload_file(local_path, BUCKET, r2_key)
        print(f'Uploaded {local_path} -> {r2_key}')
    except Exception as e:
        print(f'Error uploading {local_path}: {e}')

print('Done!')
