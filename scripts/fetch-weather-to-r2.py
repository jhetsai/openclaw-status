#!/usr/bin/env python3
"""Fetch WeatherAPI data and save to R2"""
import urllib.request, json, boto3, os

API_KEY = os.environ.get('WEATHER_API_KEY') or ''
LAT, LON = 23.71, 120.29
URL = f"https://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={LAT},{LON}&days=7&aqi=no&alerts=no"

response = urllib.request.urlopen(URL, timeout=15)
data = json.loads(response.read())

s3 = boto3.client('s3', endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
    aws_access_key_id=os.environ.get('R2_ACCESS_KEY'),
    aws_secret_access_key=os.environ.get('R2_SECRET_KEY'))

content = json.dumps(data, ensure_ascii=False)
s3.put_object(Bucket='shared-files', Key='weather-api/current.json', Body=content.encode('utf-8'), ContentType='application/json')

now = data['location']['localtime']
current = data['current']
print(f"OK - {now}, {current['temp_c']}°C, {current['condition']['text']}, Wind {current['wind_kph']}km/h")
