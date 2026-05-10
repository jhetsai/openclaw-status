#!/usr/bin/env python3
import boto3
import sys
import os

# R2 credentials from ~/.api_keys
API_KEYS_FILE = os.path.expanduser('~/.api_keys')
if os.path.exists(API_KEYS_FILE):
    with open(API_KEYS_FILE) as f:
        for line in f:
            line = line.strip()
            if line.startswith('R2_ACCESS_KEY='):
                ACCESS_KEY = line.split('=', 1)[1].strip()
            elif line.startswith('R2_SECRET_KEY='):
                SECRET_KEY = line.split('=', 1)[1].strip()
else:
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
    
    # Determine R2 key: use relative path if it's in a subdirectory
    # e.g. "assets/index.html" → key="assets/index.html"; "/home/user/file.txt" → key="assets/file.txt" (relative to workspace)
    import pathlib
    WORKSPACE = '/home/jhe/.openclaw/workspace'
    # Strip leading sep for absolute paths, then check if it's under workspace
    clean_path = file_path.lstrip(os.sep)
    if file_path.startswith(os.sep):
        # Absolute path - try to make it relative to WORKSPACE
        if clean_path.startswith(WORKSPACE.lstrip(os.sep)):
            key = clean_path[len(WORKSPACE.lstrip(os.sep)):].lstrip(os.sep)
        else:
            key = clean_path
    else:
        # Relative path
        key = clean_path.lstrip('./')
    
    # Fallback: if no separator, use just filename
    if os.sep not in key and '/' not in key:
        key = file_name
    
    try:
        s3.upload_file(file_path, BUCKET, key)
        url = f"https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev/{key}"
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
