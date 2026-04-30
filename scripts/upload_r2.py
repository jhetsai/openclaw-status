#!/usr/bin/env python3
import boto3
import sys
import os

# R2 credentials
ACCESS_KEY = os.environ.get('R2_ACCESS_KEY')
SECRET_KEY = os.environ.get('R2_SECRET_KEY')
ENDPOINT = 'https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com'
BUCKET = 'shared-files'

def upload_file(file_path):
    if not os.path.exists(file_path):
        print(f"檔案不存在: {file_path}")
        return False
    
    s3 = boto3.client(
        's3',
        endpoint_url=ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY
    )
    
    file_name = os.path.basename(file_path)
    
    try:
        s3.upload_file(file_path, BUCKET, file_name)
        url = f"https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/{file_name}"
        print(f"上傳成功！")
        print(f"下載連結：{url}")
        return True
    except Exception as e:
        print(f"上傳失敗：{e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法：python3 upload_r2.py <檔案路徑>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    upload_file(file_path)
