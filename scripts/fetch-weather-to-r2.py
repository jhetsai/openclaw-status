#!/usr/bin/env python3
"""Fetch WeatherAPI data and save to R2"""
import os, json, boto3

# Source API keys from ~/.api_keys
try:
    with open(os.path.expanduser("~/.api_keys")) as f:
        for line in f:
            if line.strip() and not line.startswith("#") and "=" in line:
                k, v = line.strip().split("=", 1)
                os.environ[k.strip()] = v.strip()
except:
    pass

API_KEY = os.environ.get('WEATHER_API_KEY') or ''
LAT, LON = 23.71, 120.29
R2_BUCKET = 'shared-files'
R2_ENDPOINT = 'https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com'

def fetch_weather():
    url = f'https://api.weatherapi.com/v1/current.json?key={API_KEY}&q={LAT},{LON}&aqi=no'
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'Weather fetch error: {e}')
        return None

import urllib.request
data = fetch_weather()
if data:
    with open('/tmp/weather.json', 'w') as f:
        json.dump(data, f, ensure_ascii=False)
    
    s3 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=os.environ.get('R2_ACCESS_KEY'),
        aws_secret_access_key=os.environ.get('R2_SECRET_KEY'))
    s3.upload_file('/tmp/weather.json', R2_BUCKET, 'weather.json', 
        ExtraArgs={'ContentType': 'application/json'})
    print(f"Weather updated: {data['current']['temp_c']}°C")
else:
    print('Weather fetch failed')
