#!/usr/bin/env python3
"""Fetch WeatherAPI + Windy GFS data and save to R2"""
import boto3, os, json

# Source API keys from ~/.api_keys
try:
    with open(os.path.expanduser("~/.api_keys")) as f:
        for line in f:
            if line.strip() and not line.startswith("#") and "=" in line:
                k, v = line.strip().split("=", 1)
                os.environ[k.strip()] = v.strip()
except:
    pass

ACCESS_KEY = os.environ.get('R2_ACCESS_KEY')
SECRET_KEY = os.environ.get('R2_SECRET_KEY')

def s3_client():
    return boto3.client('s3', endpoint_url='https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com',
        aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

API_KEY = os.environ.get('WEATHER_API_KEY') or ''
WINDY_KEY = os.environ.get('WINDY_KEY') or ''
LAT, LON = 23.6052, 120.2386  # 水林家（你家座標）
R2_BUCKET = 'shared-files'
R2_ENDPOINT = 'https://83de8038b42470b0576833e6d30e926d.r2.cloudflarestorage.com'

def fetch_weather():
    url = f'https://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={LAT},{LON}&days=3&aqi=no&alerts=no'
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'WeatherAPI error: {e}')
        return None

def fetch_windy():
    """Fetch Windy GFS point forecast for 18 hours"""
    if not WINDY_KEY:
        print('WINDY_KEY not set, skipping')
        return None
    body = {
        'lat': LAT, 'lon': LON, 'model': 'gfs',
        'parameters': ['precip', 'temp', 'rh', 'wind', 'windGust', 'pressure'],
        'levels': ['surface'], 'key': WINDY_KEY
    }
    try:
        req = urllib.request.Request('https://api.windy.com/api/point-forecast/v2',
            data=json.dumps(body).encode(),
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'Windy error: {e}')
        return None

import urllib.request

# 1. WeatherAPI
data = fetch_weather()
if data:
    with open('/tmp/weather.json', 'w') as f:
        json.dump(data, f, ensure_ascii=False)
    s3 = s3_client()
    content = json.dumps(data, ensure_ascii=False)
    s3.put_object(Bucket=R2_BUCKET, Key='weather-api/current.json', Body=content.encode('utf-8'),
                  ContentType='application/json')
    print(f'WeatherAPI: {data["current"]["temp_c"]}°C -> R2: weather-api/current.json')
else:
    print('WeatherAPI fetch failed')

# 2. Open-Meteo hourly 預報（先抓，給 Windy 段填 rain_mm_h 用）
def fetch_openmeteo_hourly():
    """抓 Open-Meteo 小時降雨預報（不含 daily，for real-time 填入）
    2026-06-04 新增：因為 Windy GFS 對台灣不給 forecast precip"""
    url = (f'https://api.open-meteo.com/v1/forecast'
           f'?latitude=23.6052&longitude=120.2386'
           f'&hourly=precipitation,precipitation_probability'
           f'&timezone=Asia/Taipei&forecast_days=4')
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'Open-Meteo hourly error: {e}')
        return None

om_hourly = fetch_openmeteo_hourly()
om_rain_map = {}  # ts_ms (UTC) -> precipitation mm
if om_hourly:
    from datetime import datetime, timezone, timedelta
    TW = timezone(timedelta(hours=8))
    for t_str, r in zip(om_hourly.get('hourly', {}).get('time', []),
                        om_hourly.get('hourly', {}).get('precipitation', [])):
        try:
            # Open-Meteo time: "2026-06-04T08:00" 是 Asia/Taipei 時間
            naive = datetime.fromisoformat(t_str)
            local_tw = naive.replace(tzinfo=TW)
            ts_ms = int(local_tw.timestamp() * 1000)
            om_rain_map[ts_ms] = r
        except Exception as e:
            print(f'  Parse error for {t_str}: {e}')
    print(f'Open-Meteo hourly: {len(om_rain_map)} hours loaded (for rain_mm_h filling)')

# 3. Windy GFS
windy = fetch_windy()
if windy:
    # 2026-06-04 修正說明：
    # Windy GFS 對台灣不提供 forecast precip（precip-surface 是空陣列）
    # 改用 Open-Meteo hourly 填 rain_mm_h（多模型融合，對台灣降雨準）
    # 其他欄位（temp, rh, wind, pressure）仍用 Windy GFS
    ts = windy.get('ts', [])
    rain = windy.get('past3hprecip-surface', [])  # 雖有但不用
    temp = windy.get('temp-surface', [])
    rh = windy.get('rh-surface', [])
    u = windy.get('wind_u-surface', [])
    v = windy.get('wind_v-surface', [])
    gust = windy.get('gust-surface', [])
    press = windy.get('pressure-surface', [])
    
    # 整理成每小時陣列
    hourly_data = []
    for i in range(len(ts)):
        import math
        # 2026-06-04 修正：rain_mm_h 改用 Open-Meteo（對齊時戳）
        # ts[i] 是 UTC ms，Open-Meteo map key 也是 UTC ms
        rain_h = om_rain_map.get(ts[i], 0.0)
        if not om_rain_map:
            # 沒有 Open-Meteo 資料時，fallback 給 0（不要用 Windy past3h 以免誤導）
            rain_h = 0.0
        temp_c = (temp[i] - 273.15) if i < len(temp) else None
        rh_val = rh[i] if i < len(rh) else None
        u_val = u[i] if i < len(u) else 0
        v_val = v[i] if i < len(v) else 0
        gust_val = gust[i] if i < len(gust) else 0
        press_val = press[i] if i < len(press) else 0
        
        angle = math.atan2(-u_val, -v_val) * 180 / math.pi
        dir8 = ['N','NE','E','SE','S','SW','W','NW']
        wind_dir = dir8[int((angle+360)%360/45)]
        hourly_data.append({
            'ts': ts[i],
            'rain_mm_h': round(rain_h, 4),  # 來自 Open-Meteo（不是 Windy）
            'temp_c': round(temp_c, 1) if temp_c is not None else None,
            'rh': round(rh_val, 0) if rh_val is not None else None,
            'wind_dir': wind_dir,
            'wind_kph': round(abs(math.sqrt(u_val**2 + v_val**2))*3.6, 1),
            'gust_kph': round(gust_val*3.6, 1),
            'pressure_hPa': round(press_val, 0)
        })
    
    # 2026-06-04 修正：加 metadata 備注
    windy_out = {
        'fetched_at': __import__('datetime').datetime.now().isoformat(),
        'location': {'lat': LAT, 'lon': LON},
        'rain_source': 'Open-Meteo (multi-model: GFS+ECMWF+ICON blend, hourly forecast)',
        'wind_source': 'Windy GFS (forecast for temp/rh/wind/pressure)',
        'notes': 'rain_mm_h 來自 Open-Meteo（小時預報）；其他欄位（temp_c, rh, wind_dir, wind_kph, gust_kph, pressure_hPa）來自 Windy GFS',
        'reason': 'Windy GFS 對台灣不提供 forecast precip (precip-surface 是空陣列)，所以降雨量用 Open-Meteo',
        'hourly': hourly_data
    }
    
    with open('/tmp/windy.json', 'w') as f:
        json.dump(windy_out, f, ensure_ascii=False)
    s3 = s3_client()
    s3.put_object(Bucket=R2_BUCKET, Key='weather-api/windy-gfs.json', Body=json.dumps(windy_out, ensure_ascii=False).encode('utf-8'),
                  ContentType='application/json')
    
    # 未來6h累計雨量（用 Open-Meteo 填的 rain_mm_h 加總）
    future6h = sum(h['rain_mm_h'] for h in hourly_data[:6])
    print(f'Windy GFS (rain from Open-Meteo): {len(ts)} records, 未來6h雨量={future6h:.2f}mm -> R2: weather-api/windy-gfs.json')
else:
    print('Windy fetch failed')

# 4. Open-Meteo 10 日預報（daily，台灣降雨最準確的來源）
def fetch_openmeteo():
    url = (f'https://api.open-meteo.com/v1/forecast'
           f'?latitude=23.6052&longitude=120.2386'
           f'&daily=precipitation_sum,precipitation_probability_max,weather_code,'
           f'temperature_2m_max,temperature_2m_min,wind_speed_10m_max'
           f'&timezone=Asia/Taipei&forecast_days=10')
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'Open-Meteo error: {e}')
        return None

om = fetch_openmeteo()
if om:
    om_out = {
        'fetched_at': __import__('datetime').datetime.now().isoformat(),
        'location': {'lat': 23.6052, 'lon': 120.2386, 'name': '水林'},
        'daily': om.get('daily', {}),
        'source': 'Open-Meteo (multi-model: GFS+ECMWF+ICON blend)'
    }
    s3 = s3_client()
    s3.put_object(Bucket=R2_BUCKET, Key='weather-api/openmeteo-forecast.json',
                  Body=json.dumps(om_out, ensure_ascii=False).encode('utf-8'),
                  ContentType='application/json')
    daily = om.get('daily', {})
    total_rain = sum(daily.get('precipitation_sum', []))
    n_days = len(daily.get('time', []))
    print(f'Open-Meteo: {n_days} days, 10日總降雨={total_rain:.1f}mm -> R2: weather-api/openmeteo-forecast.json')
else:
    print('Open-Meteo fetch failed')
