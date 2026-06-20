#!/usr/bin/env python3
"""
CWA Weather to R2 - 將 CWA 鄉鎮預報打包成 JSON 上傳到 R2
來源：CWA OpenData F-D0047-025 (雲林縣鄉鎮預報)
輸出：weather-api/cwa-forecast.json
"""
import json
import os
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

def get_creds():
    creds = {}
    try:
        with open(os.path.expanduser('~/.api_keys')) as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    k, v = line.strip().split('=', 1)
                    creds[k.strip()] = v.strip()
    except Exception:
        pass
    return creds

def fetch_cwa():
    creds = get_creds()
    key = creds.get('CWA_API_KEY')
    if not key:
        return None, 'No CWA_API_KEY'
    
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-025?Authorization={key}&format=JSON&LocationName={urllib.parse.quote('水林鄉')}"
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            return json.load(resp), None
    except Exception as e:
        return None, str(e)

def parse_cwa(raw):
    locs = raw.get('records', {}).get('Locations', [])
    if not locs: return None
    loc = locs[0]['Location'][0]
    elem_map = {e['ElementName']: e for e in loc.get('WeatherElement', [])}

    # 定義時間軸 (用 3hr-block 做主軸)
    # 3小時降雨機率 32 點 (4天 * 8時段)
    time_axis = None
    for ename in ['3小時降雨機率', '天氣現象', '風速']:
        if ename in elem_map and elem_map[ename].get('Time'):
            time_axis = elem_map[ename]['Time']
            break
    if not time_axis: return None

    hourly = []
    for t in time_axis:
        # CWA 不同欄位時間格式不同，優先用 StartTime (3hr block)
        dt = t.get('StartTime', t.get('DataTime', ''))
        if not dt: continue
        
        rec = {'time': dt}
        # 溫度類 (1hr-interval, 需找區間內的代表值)
        def get_val(ename, key, field='DataTime'):
            if ename not in elem_map: return None
            e = elem_map[ename]
            for item in e.get('Time', []):
                if item.get(field) == dt or (field=='DataTime' and dt in item.get('DataTime', '')):
                    v = item.get('ElementValue', [{}])[0].get(key)
                    if not v or v == 'N/A': return None
                    try: return float(v)
                    except (ValueError, TypeError): return v
            return None

        rec['temp_c'] = get_val('溫度', 'Temperature')
        rec['feels_like_c'] = get_val('體感溫度', 'ApparentTemperature')
        rec['rh'] = get_val('相對濕度', 'RelativeHumidity')
        rec['wind_speed_ms'] = get_val('風速', 'WindSpeed')
        rec['wind_dir'] = get_val('風向', 'WindDirection')
        rec['weather'] = get_val('天氣現象', 'Weather', 'StartTime')
        rec['precip_3h_pct'] = get_val('3小時降雨機率', 'ProbabilityOfPrecipitation', 'StartTime')
        hourly.append(rec)

    # Daily aggregate
    daily = []
    by_date = {}
    for h in hourly:
        date = h['time'][:10]
        if date not in by_date: by_date[date] = {'temps': [], 'precips': [], 'weathers': []}
        if 'temp_c' in h and h['temp_c']: by_date[date]['temps'].append(h['temp_c'])
        if 'precip_3h_pct' in h and h['precip_3h_pct']: by_date[date]['precips'].append(h['precip_3h_pct'])
        if 'weather' in h: by_date[date]['weathers'].append(h['weather'])

    for d in sorted(by_date.keys()):
        rec = by_date[d]
        daily.append({
            'date': d,
            'high': max(rec['temps']) if rec['temps'] else None,
            'low': min(rec['temps']) if rec['temps'] else None,
            'max_precip_3h_pct': max(rec['precips']) if rec['precips'] else None,
            'weather': rec['weathers'][0] if rec['weathers'] else '?'
        })

    return {
        'fetched_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
        'source': 'CWA F-D0047-025',
        'location': {'name': '水林鄉', 'lat': 23.6052, 'lon': 120.2386},
        'current': hourly[0] if hourly else {},
        'hourly': hourly,
        'daily': daily
    }

def upload_r2(data):
    creds = get_creds()
    import boto3
    s3 = boto3.client('s3', 
        endpoint_url=f"https://{creds.get('R2_ACCOUNT_ID', '83de8038b42470b0576833e6d30e926d')}.r2.cloudflarestorage.com",
        aws_access_key_id=creds.get('R2_ACCESS_KEY'),
        aws_secret_access_key=creds.get('R2_SECRET_KEY'))
    s3.put_object(Bucket=creds.get('R2_BUCKET', 'shared-files'), 
                  Key='weather-api/cwa-forecast.json', 
                  Body=json.dumps(data, ensure_ascii=False).encode('utf-8'),
                  ContentType='application/json')

if __name__ == '__main__':
    raw, err = fetch_cwa()
    if raw:
        data = parse_cwa(raw)
        if data:
            upload_r2(data)
            print(f'✅ Uploaded CWA forecast to R2 at {datetime.now()}')
    else:
        print(f'❌ Error: {err}')
