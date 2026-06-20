import boto3, os

creds = {}
with open(os.path.expanduser('~/.api_keys')) as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            creds[k.strip()] = v.strip()

ACCESS_KEY = creds.get('R2_ACCESS_KEY', '')
SECRET_KEY = creds.get('R2_SECRET_KEY', '')
R2_ACCOUNT = creds.get('R2_ACCOUNT_ID', '83de8038b42470b0576833e6d30e926d')
BUCKET = creds.get('R2_BUCKET', 'shared-files')

html_path = '/home/jhe/.openclaw/workspace/agri-weather/index.html'
with open(html_path) as f:
    content = f.read()

s3 = boto3.client('s3', endpoint_url=f'https://{R2_ACCOUNT}.r2.cloudflarestorage.com',
    aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

s3.put_object(Bucket=BUCKET, Key='agri-weather/index.html',
    Body=content.encode('utf-8'), ContentType='text/html',
    CacheControl='max-age=300')
print('✅ 上傳完成')