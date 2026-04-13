#!/usr/bin/env python3
import boto3
import sys
import os

ACCESS_KEY = 'R2_ACCESS_KEY_REDACTED'
SECRET_KEY = 'R2_SECRET_KEY_REDACTED'
ENDPOINT = 'https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com'
BUCKET = 'shared-files'
PUBLIC_URL = 'https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev'

def upload_file(file_path, dest_key=None):
    if not os.path.exists(file_path):
        print(f"❌ 檔案不存在: {file_path}")
        return None
    
    s3 = boto3.client(
        's3',
        endpoint_url=ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY
    )
    
    key = dest_key or os.path.basename(file_path)
    content_type = _get_content_type(key)
    
    try:
        s3.upload_file(file_path, BUCKET, key, ExtraArgs={'ContentType': content_type})
        url = f"{PUBLIC_URL}/{key}"
        return (key, url)
    except Exception as e:
        print(f"❌ 上傳失敗：{e}")
        return None


def _get_content_type(key):
    if key.endswith('.html'): return 'text/html'
    if key.endswith('.pdf'): return 'application/pdf'
    if key.endswith('.png'): return 'image/png'
    if key.endswith('.jpg') or key.endswith('.jpeg'): return 'image/jpeg'
    if key.endswith('.css'): return 'text/css'
    if key.endswith('.js'): return 'application/javascript'
    if key.endswith('.ico'): return 'image/x-icon'
    return 'application/octet-stream'

def delete_file(file_name):
    s3 = boto3.client(
        's3',
        endpoint_url=ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY
    )
    
    try:
        s3.delete_object(Bucket=BUCKET, Key=file_name)
        return True
    except Exception as e:
        print(f"❌ 刪除失敗：{e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法：")
        print("  python3 r2_tool.py upload <檔案路徑>")
        print("  python3 r2_tool.py delete <檔案名稱>")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == 'upload':
        if len(sys.argv) < 3:
            print("❌ 請提供檔案路徑")
            sys.exit(1)
        dest = sys.argv[3] if len(sys.argv) > 3 else None
        result = upload_file(sys.argv[2], dest)
        if result:
            file_name, url = result
            print(f"✅ 上傳成功！")
            print(f"下載連結：{url}")
            print(f"檔案名稱：{file_name}")
    elif action == 'delete':
        if delete_file(sys.argv[2]):
            print(f"✅ 已刪除：{sys.argv[2]}")
    else:
        print(f"❌ 未知動作：{action}")
        print(f"""
用法：
  python3 r2_tool.py upload <檔案路徑> [R2目標路徑]
  python3 r2_tool.py delete <檔案名稱>

範例：
  python3 r2_tool.py upload stock_portfolio.html stock/index.html
  python3 r2_tool.py upload report.pdf reports/report.pdf
  python3 r2_tool.py delete old_file.pdf
""")
