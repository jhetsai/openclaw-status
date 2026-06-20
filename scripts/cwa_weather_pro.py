#!/usr/bin/env python3
"""
CWA Weather API - 即時天氣查詢 (雲林縣水林鄉)
使用 CWA OpenData API
- O-A0001-001: 即時觀測 (各測站)
- F-D0047-025: 雲林縣未來 3 天鄉鎮預報
"""
import json, os, urllib.request
from datetime import datetime

def get_cwa_key():
    """Get CWA API key from ~/.api_keys"""
    try:
        with open('/home/jhe/.api_keys', 'r') as f:
            for line in f:
                if line.startswith('CWA_API_KEY='):
                    return line.split('=')[1].strip()
    except:
        pass
    return os.environ.get('CWA_API_KEY', '')

def fetch_cwa(dataset_id, params=None):
    """Fetch data from CWA OpenData API"""
    key = get_cwa_key()
    if not key:
        return None, "No CWA API key found"
    
    base = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"
    url = f"{base}/{dataset_id}?Authorization={key}&format=JSON"
    if params:
        for k, v in params.items():
            url += f"&{k}={urllib.parse.quote(str(v))}"
    
    try:
        with urllib.request.urlopen(url) as resp:
            return json.load(resp), None
    except Exception as e:
        return None, str(e)

import urllib.parse

def get_yunlin_observation():
    """Get real-time observation from Yunlin County stations"""
    data, err = fetch_cwa("O-A0001-001")
    if err or not data.get('success'):
        return None, err or data.get('message', 'API failed')
    
    stations = data.get('records', {}).get('Station', [])
    # Find Yunlin stations
    yl_stations = [s for s in stations if s.get('GeoInfo', {}).get('CountyName') == '雲林縣']
    
    if not yl_stations:
        return None, "No Yunlin stations found"
    
    return yl_stations, None

def get_shuilin_forecast():
    """Get forecast for Shuilin Township, Yunlin County (F-D0047-025)"""
    data, err = fetch_cwa("F-D0047-025")
    if err or not data.get('success'):
        return None, err or data.get('message', 'API failed')
    
    locations = data.get('records', {}).get('Locations', [])
    if not locations:
        return None, "No locations data"
    
    yl_loc = locations[0]  # F-D0047-025 is 雲林 only
    for sub in yl_loc.get('Location', []):
        if sub.get('LocationName') == '水林鄉':
            return sub, None
    
    return None, "水林鄉 not found"

def extract_value(elem_value_list, key):
    """Extract specific value from ElementValue list"""
    if not elem_value_list or not isinstance(elem_value_list, list):
        return 'N/A'
    first = elem_value_list[0]
    if isinstance(first, dict):
        return first.get(key, 'N/A')
    return 'N/A'

def get_nearest_forecast(elem, current_hour):
    """Get the forecast value nearest to current hour"""
    times = elem.get('Time', [])
    if not times:
        return None, None
    
    # Each time has DataTime - find one matching current hour
    for t in times:
        dt = t.get('DataTime', '')
        if dt:
            try:
                hour_str = dt[11:13]
                if hour_str == current_hour:
                    return t, dt
            except:
                pass
    # Fallback: return first
    return times[0], times[0].get('DataTime', '')

def format_observation(stations):
    """Format real-time observation report"""
    if not stations:
        return "❌ 無觀測資料"
    
    # Try to find a station with valid data
    valid_stations = []
    for s in stations:
        we = s.get('WeatherElement', {})
        if isinstance(we, dict) and we.get('AirTemperature'):
            valid_stations.append(s)
    
    if not valid_stations:
        # All stations have empty WeatherElement - report that
        lines = []
        lines.append("📡 **CWA 即時觀測（雲林縣）**")
        lines.append("⚠️ 所有觀測站目前都沒有有效即時資料")
        lines.append("")
        lines.append("可用站點：")
        for s in stations[:5]:
            name = s.get('StationName', 'N/A')
            town = s.get('GeoInfo', {}).get('TownName', 'N/A')
            lines.append(f"  • {name} ({town})")
        return '\n'.join(lines)
    
    # Use the first valid station
    s = valid_stations[0]
    name = s.get('StationName', '未知站')
    town = s.get('GeoInfo', {}).get('TownName', '未知鄉鎮')
    we = s.get('WeatherElement', {})
    obs_time = s.get('ObsTime', {}).get('DateTime', 'N/A')
    
    lines = []
    lines.append(f"📡 **CWA 即時觀測 - {name} ({town})**")
    lines.append(f"🕐 觀測時間: {obs_time}")
    lines.append("")
    lines.append(f"- 🌡️ 溫度: {we.get('AirTemperature', 'N/A')}°C")
    lines.append(f"- 💧 露點: {we.get('DewPoint', 'N/A')}°C")
    lines.append(f"- 💦 相對濕度: {we.get('RelativeHumidity', 'N/A')}%")
    lines.append(f"- 💨 風速: {we.get('WindSpeed', 'N/A')} m/s")
    lines.append(f"- 🧭 風向: {we.get('WindDirection', 'N/A')}°")
    lines.append(f"- ☁️ 天氣: {we.get('Weather', 'N/A')}")
    precip = we.get('Now', {}).get('Precipitation', 'N/A') if isinstance(we.get('Now'), dict) else 'N/A'
    lines.append(f"- 🌧️ 降雨量: {precip} mm")
    return '\n'.join(lines)

def format_forecast(sl_data, current_hour=None):
    """Format Shuilin forecast report"""
    if not sl_data:
        return "❌ 無預報資料"
    
    if current_hour is None:
        current_hour = datetime.now().strftime("%H")
    
    lines = []
    lines.append(f"🔮 **水林鄉未來3天鄉鎮預報 (F-D0047-025)**")
    
    # Get all 3-hour forecast, current temp
    we_list = sl_data.get('WeatherElement', [])
    elem_map = {e.get('ElementName'): e for e in we_list}
    
    # Current hour
    lines.append(f"\n🕐 **現在時刻 ({current_hour}:00)**")
    for ename in ['溫度', '體感溫度', '相對濕度', '風速', '風向', '天氣現象', '3小時降雨機率', '天氣預報綜合描述']:
        if ename in elem_map:
            elem = elem_map[ename]
            t, dt = get_nearest_forecast(elem, current_hour)
            if t:
                val = t.get('ElementValue', [{}])[0]
                # Different fields have different keys
                if ename == '溫度':
                    v = val.get('Temperature', 'N/A')
                    lines.append(f"  • {ename}: {v}°C")
                elif ename == '體感溫度':
                    v = val.get('ApparentTemperature', 'N/A')
                    lines.append(f"  • {ename}: {v}°C")
                elif ename == '相對濕度':
                    v = val.get('RelativeHumidity', 'N/A')
                    lines.append(f"  • {ename}: {v}%")
                elif ename == '風速':
                    v = val.get('WindSpeed', 'N/A')
                    lines.append(f"  • {ename}: {v} m/s")
                elif ename == '風向':
                    v = val.get('WindDirection', 'N/A')
                    lines.append(f"  • {ename}: {v}")
                elif ename == '天氣現象':
                    v = val.get('Weather', 'N/A')
                    lines.append(f"  • {ename}: {v}")
                elif ename == '3小時降雨機率':
                    v = val.get('ProbabilityOfPrecipitation', 'N/A')
                    lines.append(f"  • {ename}: {v}%")
                elif ename == '天氣預報綜合描述':
                    v = val.get('WeatherDescription', 'N/A')
                    lines.append(f"  • {ename}: {v}")
    
    # Today's high/low
    if '溫度' in elem_map:
        lines.append(f"\n📊 **未來36小時溫度變化**")
        temp_elem = elem_map['溫度']
        times = temp_elem.get('Time', [])
        for t in times[:13]:  # Show next ~12 hours (every 3hr)
            dt = t.get('DataTime', '')
            val = t.get('ElementValue', [{}])[0]
            temp = val.get('Temperature', '?')
            time_str = dt[5:16] if dt else 'N/A'
            lines.append(f"  {time_str}: {temp}°C")
    
    return '\n'.join(lines)

def get_weather_report():
    """Main function - get full weather report"""
    report = []
    report.append("=" * 50)
    report.append("🌦️ CWA 即時天氣報告 - 雲林縣水林鄉")
    report.append(f"⏰ 查詢時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 50)
    report.append("")
    
    # 1. Real-time observation
    stations, err = get_yunlin_observation()
    if err:
        report.append(f"❌ 觀測資料取得失敗: {err}")
    else:
        report.append(format_observation(stations))
    report.append("")
    
    # 2. Forecast
    sl, err2 = get_shuilin_forecast()
    if err2:
        report.append(f"❌ 預報資料取得失敗: {err2}")
    else:
        report.append(format_forecast(sl))
    
    return '\n'.join(report)

if __name__ == "__main__":
    print(get_weather_report())