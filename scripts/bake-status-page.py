#!/usr/bin/env python3
"""Bake API + weather data into the status HTML page."""
import sys, json, re, os
from datetime import datetime

html_path = sys.argv[1]
api_path = sys.argv[2]
wx_path = sys.argv[3]

TS = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

with open(html_path) as f:
    c = f.read()
with open(api_path) as f:
    d = json.load(f)
with open(wx_path) as f:
    w = json.load(f)

def rpl(label, new_val):
    global c
    pattern = r'(<div class="label">' + re.escape(label) + r'</div><div class="value">)[^<]*'
    c = re.sub(pattern, lambda m: m.group(1) + new_val, c)

# Bake system info
rpl('開機時間', d.get('uptime', '-') or '-')
mem_used = round(float(d.get('memUsed', 0)), 1)
mem_tot = round(float(d.get('memTotal', 0)), 1)
rpl('記憶體', f"{mem_used} / {mem_tot} GB")
rpl('CPU 使用率', f"{round(float(d.get('cpuPercent', 0)), 1)}%")

# Bake weather
current = w.get('current', {})
temp = current.get('temperature_2m', '?')
wind = current.get('windspeed_10m', '?')
code = current.get('weathercode', 0)

wx_map = {0:'晴',1:'晴',2:'多雲',3:'多雲',45:'霧',48:'霧',51:'毛毛雨',53:'毛毛雨',55:'毛毛雨',61:'雨',63:'雨',65:'雨',71:'雪',73:'雪',75:'雪',80:'雨',81:'雨',82:'雨',95:'雷雨',96:'雷雨',99:'雷雨'}
wtxt = wx_map.get(code, '晴' if code==0 else '多雲' if code<=3 else '惡劣')

rpl('麥寮測站', '水林 ' + wtxt)
rpl('氣溫', str(temp) + '°C')
rpl('風速', str(wind) + ' km/h')
rpl('今日天氣', wtxt)

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
