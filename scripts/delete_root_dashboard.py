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

# Files to delete from root
files_to_delete = [
    'index-D5DNTjI7.js',
    'index-CmoZD0wg.js',
    'index-BAe6MO8R.js',
    'index.html',
    'index-nqMpL4T3.css',
]

for key in files_to_delete:
    try:
        s3.delete_object(Bucket=BUCKET, Key=key)
        print(f'Deleted: {key}')
    except Exception as e:
        print(f'Error deleting {key}: {e}')

print('Done!')
