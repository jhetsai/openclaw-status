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

# Upload new JS
try:
    s3.upload_file('/home/jhe/.openclaw/workspace/react-stock-dashboard/dist/assets/index-CZPaRCyA.js', BUCKET, 'dashboard/index-CZPaRCyA.js')
    print('Uploaded: dashboard/index-CZPaRCyA.js')
except Exception as e:
    print(f'Error: {e}')

# Update index.html
html = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>持股儀表板</title>
<link rel="stylesheet" href="index-nqMpL4T3.css">
<link rel="stylesheet" href="responsive.css">
</head>
<body>
<div id="root"></div>
<script src="index-CZPaRCyA.js"></script>
</body>
</html>'''

with open('/home/jhe/.openclaw/workspace/dashboard/index.html', 'w') as f:
    f.write(html)

try:
    s3.upload_file('/home/jhe/.openclaw/workspace/dashboard/index.html', BUCKET, 'dashboard/index.html')
    print('Uploaded: dashboard/index.html')
except Exception as e:
    print(f'Error: {e}')

# Delete old JS
try:
    s3.delete_object(Bucket=BUCKET, Key='dashboard/index-C9lprl4O.js')
    print('Deleted: dashboard/index-C9lprl4O.js')
except:
    pass

print('Done!')