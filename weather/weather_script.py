import json

data = {
  "latitude": 23.75, "longitude": 120.375,
  "hourly": {
    "time": ["2026-04-03T00:00","2026-04-03T01:00","2026-04-03T02:00","2026-04-03T03:00","2026-04-03T04:00","2026-04-03T05:00","2026-04-03T06:00","2026-04-03T07:00","2026-04-03T08:00","2026-04-03T09:00","2026-04-03T10:00","2026-04-03T11:00","2026-04-03T12:00","2026-04-03T13:00","2026-04-03T14:00","2026-04-03T15:00","2026-04-03T16:00","2026-04-03T17:00","2026-04-03T18:00","2026-04-03T19:00","2026-04-03T20:00","2026-04-03T21:00","2026-04-03T22:00","2026-04-03T23:00","2026-04-04T00:00","2026-04-04T01:00","2026-04-04T02:00","2026-04-04T03:00","2026-04-04T04:00","2026-04-04T05:00","2026-04-04T06:00","2026-04-04T07:00","2026-04-04T08:00","2026-04-04T09:00","2026-04-04T10:00","2026-04-04T11:00","2026-04-04T12:00","2026-04-04T13:00","2026-04-04T14:00","2026-04-04T15:00","2026-04-04T16:00","2026-04-04T17:00","2026-04-04T18:00","2026-04-04T19:00","2026-04-04T20:00","2026-04-04T21:00","2026-04-04T22:00","2026-04-04T23:00"],
    "temperature_2m": [22.9,22.8,22.5,22.6,22.5,22.3,21.9,22.1,23.0,24.6,26.3,27.9,29.2,29.7,28.6,28.3,28.2,27.8,27.1,26.4,26.0,26.0,25.6,25.4,25.5,25.2,25.0,24.9,24.7,24.2,23.9,24.2,24.8,25.2,25.1,24.8,24.6,24.5,24.2,24.2,24.1,24.1,23.9,23.6,23.5,23.5,23.5,23.4],
    "apparent_temperature": [26.8,26.3,25.9,25.8,25.7,25.4,25.1,25.5,26.4,27.1,28.3,29.6,30.7,31.4,30.0,29.2,28.3,27.8,27.5,26.4,26.6,26.6,27.1,27.4,27.7,27.8,27.5,27.6,27.6,27.1,26.9,27.0,27.8,27.4,27.0,26.9,26.9,26.8,26.3,26.6,26.8,26.8,26.5,26.0,25.9,26.1,26.3,26.4],
    "relative_humidity_2m": [85,85,88,87,87,90,92,91,87,78,72,63,57,57,64,67,70,70,73,74,77,76,79,83,84,86,86,86,87,89,90,88,85,83,83,84,85,85,86,87,87,86,88,90,90,90,90,91],
    "precipitation_probability": [10,8,13,15,23,20,10,5,0,0,0,0,0,0,3,5,5,3,3,5,15,8,15,23,33,48,33,43,60,43,48,58,85,83,83,88,95,95,98,93,93,90,90,83,80,80,82,85],
    "weather_code": [2,3,3,3,3,3,3,3,2,2,2,2,2,2,3,1,1,3,3,2,3,3,80,3,3,3,3,3,2,95,80,3,3,95,95,95,95,80,95,95,95,80,80,3,3,3,95,95],
    "wind_speed_10m": [0.5,3.1,4.2,5.2,5.8,6.7,6.5,5.2,5.2,10.8,17.7,22.0,25.5,26.0,29.3,30.1,33.9,32.9,30.4,31.2,28.4,27.0,22.1,20.8,20.6,18.1,18.4,16.9,15.9,14.7,14.0,14.9,13.9,18.5,20.3,18.9,18.0,17.7,18.7,16.8,13.8,13.4,14.9,16.6,16.5,15.5,13.8,12.2]
  }
}

# Weather code descriptions
code_map = {
    0: "☀️ 晴朗", 1: "🌤️ 大致晴朗", 2: "⛅ 部分多雲", 3: "☁️ 多雲",
    45: "🌫️ 霧", 48: "🌫️ 霧凇", 51: "🌧️ 小毛毛雨", 53: "🌧️ 毛毛雨",
    55: "🌧️ 密集毛毛雨", 61: "🌧️ 小雨", 63: "🌧️ 中雨", 65: "🌧️ 大雨",
    71: "❄️ 小雪", 73: "❄️ 中雪", 75: "❄️ 大雪", 77: "❄️ 雪粒",
    80: "🌦️ 小陣雨", 81: "🌦️ 中陣雨", 82: "🌧️ 大陣雨",
    85: "🌨️ 小雪陣", 86: "🌨️ 大雪陣", 95: "⛈️ 雷暴",
    96: "⛈️ 雷暴+冰雹", 99: "⛈️ 強雷暴+冰雹"
}

def get_desc(code):
    return code_map.get(code, f"#{code}")

# Current hour is 8:35 AM, so next 24h = index 9 to 32 (09:00 today to 08:00 tomorrow)
hourly = data["hourly"]
start_idx = 9  # 2026-04-03T09:00
end_idx = 33   # 2026-04-04T08:00 (exclusive, so 33 means up to index 32)

times = hourly["time"][start_idx:end_idx]
temps = hourly["temperature_2m"][start_idx:end_idx]
feels = hourly["apparent_temperature"][start_idx:end_idx]
humids = hourly["relative_humidity_2m"][start_idx:end_idx]
rains = hourly["precipitation_probability"][start_idx:end_idx]
codes = hourly["weather_code"][start_idx:end_idx]
winds = hourly["wind_speed_10m"][start_idx:end_idx]

# Current conditions (hour 8: 08:00)
cur_temp = hourly["temperature_2m"][7]
cur_feel = hourly["apparent_temperature"][7]
cur_humid = hourly["relative_humidity_2m"][7]
cur_rain = hourly["precipitation_probability"][7]
cur_code = hourly["weather_code"][7]
cur_wind = hourly["wind_speed_10m"][7]
cur_desc = get_desc(cur_code)

# Date
date_str = "2026/04/03"

html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<style>
body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f0f4f8; }}
.container {{ max-width: 900px; margin: 0 auto; background: white; border-radius: 16px; padding: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
h1 {{ color: #1a3a5c; text-align: center; margin-bottom: 4px; }}
.location {{ text-align: center; color: #666; font-size: 14px; margin-bottom: 20px; }}
.current-box {{ background: linear-gradient(135deg, #4a90d9, #357abd); color: white; border-radius: 16px; padding: 24px; margin-bottom: 24px; display: flex; align-items: center; gap: 20px; }}
.big-temp {{ font-size: 64px; font-weight: bold; }}
.big-desc {{ font-size: 28px; }}
.info-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 12px; }}
.info-item {{ background: rgba(255,255,255,0.2); border-radius: 10px; padding: 10px; text-align: center; }}
.info-label {{ font-size: 12px; opacity: 0.85; }}
.info-val {{ font-size: 18px; font-weight: bold; }}
table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; }}
th {{ background: #1a3a5c; color: white; padding: 10px; text-align: center; }}
td {{ padding: 8px; text-align: center; border-bottom: 1px solid #eee; }}
tr:nth-child(even) {{ background: #f8fafc; }}
tr:hover {{ background: #e8f0fa; }}
.section-title {{ color: #1a3a5c; border-left: 4px solid #4a90d9; padding-left: 12px; margin: 20px 0 12px; }}
.rain-high {{ color: #e74c3c; font-weight: bold; }}
.rain-mid {{ color: #f39c12; }}
.rain-low {{ color: #27ae60; }}
.tips {{ background: #f8f9fa; border-radius: 12px; padding: 16px; line-height: 1.8; }}
.tips li {{ margin: 6px 0; }}
.footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 20px; }}
</style>
</head>
<body>
<div class="container">
<h1>☀️ 每日天氣預報（{date_str}）</h1>
<div class="location">📍 雲林縣水林鄉</div>

<div class="current-box">
  <div class="big-temp">{cur_temp}°C</div>
  <div>
    <div class="big-desc">{cur_desc}</div>
    <div style="font-size:14px;opacity:0.85;margin-top:4px;">體感溫度 {cur_feel}°C</div>
  </div>
</div>

<div class="info-grid">
  <div class="info-item"><div class="info-label">🌡️ 體感溫度</div><div class="info-val">{cur_feel}°C</div></div>
  <div class="info-item"><div class="info-label">💧 濕度</div><div class="info-val">{cur_humid}%</div></div>
  <div class="info-item"><div class="info-label">🌧️ 降雨機率</div><div class="info-val">{cur_rain}%</div></div>
  <div class="info-item"><div class="info-label">🌬️ 風速</div><div class="info-val">{cur_wind} km/h</div></div>
</div>

<div class="section-title">⏰ 未來24小時每小時預報</div>
<table>
<tr><th>時間</th><th>天氣</th><th>溫度</th><th>體感</th><th>濕度</th><th>降雨機率</th><th>風速</th></tr>
"""

for i in range(len(times)):
    t = times[i]
    hour = t[11:16]
    rain_class = "rain-high" if rains[i] >= 60 else ("rain-mid" if rains[i] >= 30 else "rain-low")
    html += f"<tr><td>{hour}</td><td>{get_desc(codes[i])}</td><td>{temps[i]}°C</td><td>{feels[i]}°C</td><td>{humids[i]}%</td><td class='{rain_class}'>{rains[i]}%</td><td>{winds[i]} km/h</td></tr>"

html += """
</table>

<div class="section-title">👗 穿著建議</div>
<div class="tips">
<ul>
<li>🩴 上午炎熱潮濕，建議穿著輕薄透氣衣物，攜帶防曬用品</li>
<li>🌧️ 下午時段（14:00起）降雨機率逐漸升高，建議出門攜帶雨具</li>
<li>🌧️ 明日（4/4）全天降雨機率高，建議預留備用衣物</li>
<li>💧 高濕度環境（85%以上），注意防潮防霉</li>
<li>🌬️ 午後風力明顯增強（25-34 km/h），戶外活動注意安全</li>
<li>⛈️ 明日午後可能出現雷陣雨，請留意天氣變化</li>
<li>🏠 建議室內開啟除濕機維持舒適度</li>
</ul>
</div>

<div class="footer">資料來源：Open-Meteo API｜生成時間：2026-04-03 08:35</div>
</div>
</body>
</html>
"""

with open(f"/home/jhe/.openclaw/workspace/weather_2026-04-03.html", "w") as f:
    f.write(html)
print("HTML generated successfully")
