#!/usr/bin/env python3
"""Bake system API + CWA weather into the status HTML page."""
import sys, json, re, os
from datetime import datetime

html_path = sys.argv[1]
api_path = sys.argv[2]

TS = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

with open(html_path) as f:
    c = f.read()

# Fetch weather from CWA (Taiwan weather bureau)
# Use 箔子寮 station (nearest to 水林)
CWA_API = 'CWA_API_KEY_REDACTED'
CWA_URL = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization={CWA_API}'

try:
    import urllib.request
    with urllib.request.urlopen(CWA_URL, timeout=20) as resp:
        w = json.loads(resp.read())
    
    # Find nearest station to 水林
    # Prefer stations in order (first match wins)
    target_names = ['雲林東勢', '箔子寮', '高鐵雲林', '虎尾', '斗六']
    st = None
    for preferred in target_names:
        for s in (w.get('records', {}).get('Station') or []):
            sn = s.get('StationName', '')
            if isinstance(sn, dict):
                sn_str = sn.get('Zh_tw', '') or sn.get('En', '')
            else:
                sn_str = str(sn)
            if preferred in sn_str:
                st = s
                break
        if st:
            break
    
    if st:
        elem = st.get('WeatherElement', {})
        temp = elem.get('AirTemperature', '?')
        wind = elem.get('WindSpeed', '?')
        weather = st.get('WeatherElement', {}).get('Weather', '?')
        station = st.get('StationName', '?')
        
        # Convert m/s to km/h
        if wind != '?' and wind != '-99' and wind != '-':
            try:
                wind_kmh = float(wind) * 3.6
                wind = f"{wind_kmh:.1f}"
            except:
                pass
        
        print(f"CWA Weather OK: {station} {temp}°C {wind}km/h")
    else:
        temp = wind = '?'
        weather = '?'
        station = '水林'
        print("CWA: No nearby station found")
except Exception as e:
    temp = wind = '?'
    weather = '晴'
    station = '水林'
    print(f"CWA fetch failed: {e}")

# Weather description mapping for CWA
wx_map = {
    '晴': '晴', '晴(CI)': '晴', '少雲': '多雲', '多雲': '多雲', '陰': '陰',
    '陰有雨': '雨', '陰有雷雨': '雷雨', '陰有雷': '雷雨', '雨': '雨', '雷雨': '雷雨',
    '霧': '霧', '雪': '雪', '有霧': '霧', '毛毛雨': '毛毛雨', '陣雨': '雨', '雷暴': '雷雨'
}
wtxt = wx_map.get(weather, '晴' if weather and weather not in ['?', '-99'] else '晴')

# Compute solar efficiency from weather
wx_eff_map = {
    '晴': ('85W (100%)', '#2e7d32'),
    '少雲': ('60W (71%)', '#f57c00'),
    '多雲': ('50W (59%)', '#f57c00'),
    '陰': ('35W (41%)', '#f57c00'),
    '霧': ('25W (29%)', '#f57c00'),
    '雨': ('4W (5%)', '#c62828'),
    '雷雨': ('4W (5%)', '#c62828'),
    '雪': ('4W (5%)', '#c62828'),
}
# Get UV and cloud from WeatherAPI for model-based estimate
try:
    wapi_url = 'https://api.weatherapi.com/v1/current.json?key=' + os.environ.get('WEATHER_API_KEY', '') + '&q=23.71,120.29&aqi=no'
    with urllib.request.urlopen(wapi_url, timeout=10) as wr:
        wd = json.loads(wr.read())
    uv_val = wd['current']['uv']
    cloud_val = wd['current'].get('cloud', 75)
    # Time factor
    import math
    now_h = datetime.now().hour + datetime.now().minute/60
    # Solar angle model: noon at 75°, sunrise/sunset 0°
    if now_h < 5.5 or now_h > 18.5:
        solar_angle = 0
    else:
        noon_angle = 75  # max angle at noon for this lat/season
        hour_from_noon = abs(now_h - 12.2)
        solar_angle = max(0, noon_angle - hour_from_noon * 2.5)
    angle_factor = math.sin(math.radians(solar_angle))
    # Cloud factor: 75% cloud ≈ 45% transmission loss (not 75% loss)
    cloud_factor = 1 - (cloud_val / 100) * 0.6
    # Model: UV * 18.2W * cloud_factor * solar_angle_factor
    eff_w = uv_val * 18.2 * cloud_factor * angle_factor
    eff_w = min(eff_w, 85)  # cap at panel max (actual ~85W)
    eff_pct = eff_w / 85 * 100
    eff_val = f'{eff_w:.0f}W ({eff_pct:.0f}%)'
    eff_color = '#2e7d32' if eff_w > 50 else '#f57c00' if eff_w > 20 else '#c62828'
    print(f'[SolarModel] UV={uv_val} cloud={cloud_val}% angle={angle_factor:.2f} => {eff_val}')
except Exception as e:
    print(f'[SolarModel] Failed: {e}')

# Fallback: weather-based
if not eff_val:
    eff_val, eff_color = wx_eff_map.get(wtxt, ('4W (2%)', '#c62828'))

def rpl(label, new_val):
    global c
    pattern = r'(<div class="label">' + re.escape(label) + r'</div><div class="value"[^>]*>)[^<]*'
    c = re.sub(pattern, lambda m: m.group(1) + new_val, c)

rpl('麥寮測站', f'{station} {wtxt}')
rpl('氣溫', f'{temp}°C' if temp != '?' else '?°C')
rpl('風速', f'{wind} km/h' if wind != '?' else '? km/h')
rpl('今日天氣', wtxt)
rpl('發電效率', f'{eff_val}')

# Bake system info
with open(api_path) as f:
    d = json.load(f)

rpl('已開機', d.get('uptime', '-') or '-')
mem_used = round(float(d.get('memUsed', 0)), 1)
mem_tot = round(float(d.get('memTotal', 0)), 1)
rpl('記憶體', f"{mem_used} / {mem_tot} GB")
rpl('CPU 使用率', f"{round(float(d.get('cpuPercent', 0)), 1)}%")

# Bake Brave Search usage
brave_file = os.path.expanduser("~/.openclaw/brave_search_usage.json")
if os.path.exists(brave_file):
    with open(brave_file) as f:
        b = json.load(f)
    cost = b.get("cost", 0)
    limit = b.get("cost_limit", 5.0)
    display = f"${cost:.2f} / ${limit:.0f}"
    c = re.sub(r'(<tr><td>Brave Search</td><td>網路搜尋</td><td>)[^<]*(</td></tr>)',
               r'\g<1>' + display + r'\g<2>', c)

# Bake timestamps & labels
c = c.replace("📡 最後刷新時間", "📡 版本最後上傳時間")
c = re.sub(r"var ts = '[^']*';", f"var ts = '{TS}';", c)

# Remove footer
c = re.sub(r'<div class="footer">.*?</div>', '', c, flags=re.DOTALL)

with open(html_path, 'w') as f:
    f.write(c)
print(f"HTML baked OK ({TS})")
