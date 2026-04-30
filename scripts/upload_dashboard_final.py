#!/usr/bin/env python3
import boto3

ACCESS_KEY = os.environ.get('R2_ACCESS_KEY')
SECRET_KEY = os.environ.get('R2_SECRET_KEY')
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
    ('dashboard/index-nqMpL4T3.css', '/home/jhe/.openclaw/workspace/dashboard/index-nqMpL4T3.css'),
    ('dashboard/index-BP7dvtQw.js', '/home/jhe/.openclaw/workspace/react-stock-dashboard/dist/assets/index-BP7dvtQw.js'),
]

for r2_key, local_path in files:
    try:
        s3.upload_file(local_path, BUCKET, r2_key)
        print(f'Uploaded: {r2_key}')
    except Exception as e:
        print(f'Error: {e}')

# Delete old JS file
try:
    s3.delete_object(Bucket=BUCKET, Key='dashboard/index-CBMFbfwO.js')
    print('Deleted: dashboard/index-CBMFbfwO.js')
except:
    pass

print('Done!')
