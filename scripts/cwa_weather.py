#!/usr/bin/env python3
"""
CWA Weather API - Get real-time weather for Yunlin/Shuilin
Uses CWA OpenData API with token from ~/.api_keys
"""
import json, os, sys, urllib.parse, urllib.request

def get_cwa_key():
    """Get CWA API key from ~/.api_keys"""
    try:
        with open(os.path.expanduser('~/.api_keys')) as f:
            for line in f:
                if line.startswith('CWA_API_KEY='):
                    return line.split('=')[1].strip()
    except:
        pass
    # Also check environment
    return os.environ.get('CWA_API_KEY', '')

def fetch_cwa(endpoint, params=None):
    """Fetch data from CWA OpenData API"""
    key = get_cwa_key()
    if not key:
        return None, "No CWA API key found"
    
    base = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"
    url = f"{base}/{endpoint}?Authorization={key}&format=JSON"
    if params:
        url += "&" + urllib.parse.urlencode(params)
    
    try:
        with urllib.request.urlopen(url) as resp:
            return json.load(resp), None
    except Exception as e:
        return None, str(e)

def get_yunlin_town_forecast():
    """Get 36-hour forecast for Shuilin Township, Yunlin County (F-D0047-073)"""
    data, err = fetch_cwa("F-D0047-073")
    if err:
        return None, err
    
    # Navigate structure
    locations = data.get('records', {}).get('Locations', [])
    
    # Find Yunlin County
    yunlin = None
    for loc in locations:
        if loc.get('LocationsName') == '雲林縣':
            yunlin = loc
            break
    
    if not yunlin:
        return None, "Yunlin County not found"
    
    # Find Shuilin Township
    shuilin = None
    for twp in yunlin.get('Location', []):
        if twp.get('LocationName') == '水林鄉':
            shuilin = twp
            break
    
    if not shuilin:
        return None, "Shuilin Township not found"
    
    return shuilin, None

def get_current_observation():
    """Get current weather observation from automatic stations (O-A0001-001)"""
    data, err = fetch_cwa("O-A0001-001")
    if err:
        return None, err
    
    # Find stations in Yunlin
    stations = data.get('records', {}).get('Station', [])
    yunlin_stations = []
    for s in stations:
        geo = s.get('GeoInfo', {})
        if geo.get('CountyName') == '雲林縣':
            yunlin_stations.append(s)
    
    return yunlin_stations, None

def format_weather_report(shuilin_data=None, stations=None):
    """Format weather report for Shuilin"""
    lines = []
    lines.append("📍 **水林鄉（雲林縣）天氣**")
    
    if shuilin_data:
        # Get current time period
        elements = {}
        for elem in shuilin_data.get('WeatherElement', []):
            elements[elem['ElementName']] = elem.get('Time', [])
        
        # Get current time info (simplified - just show available data)
        lines.append("\n**氣象元素**：")
        for name in ['Wx', 'PoP', 'T', 'RH', 'WD', 'WS']:
            if name in elements:
                lines.append(f"- {name}: {len(elements[name])} 個預報時段")
    
    if stations:
        lines.append(f"\n**觀測站（{len(stations)} 個）**：")
        for s in stations[:3]:
            name = s.get('StationName', '')
            geo = s.get('GeoInfo', {})
            obs = s.get('WeatherElement', [])
            lines.append(f"- {name} ({geo.get('TownName', '')})")
    
    return '\n'.join(lines)

if __name__ == "__main__":
    # Test fetch
    shuilin, err = get_yunlin_town_forecast()
    obs, err2 = get_current_observation()
    
    print(format_weather_report(shuilin, obs))
