import json
import requests
from datetime import datetime
import os

# === 風速警示設定 ===
WIND_ALERT_THRESHOLD = 30  # km/h，超過此值發出警示
TELEGRAM_BOT_TOKEN = "8793435853:AAH-NCvhnOE99ENoi4sobWSNW6zEmEurrbU"
TELEGRAM_CHAT_ID = "1181571031"

def send_telegram_alert(message):
    """發送 Telegram 警示通知"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data, timeout=10)
        return True
    except Exception as e:
        print(f"Telegram 發送失敗: {e}")
        return False

# === 抓取天氣資料 ===
LAT = 23.75
LON = 120.375
API_URL = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&hourly=temperature_2m,apparent_temperature,relative_humidity_2m,precipitation_probability,weather_code,wind_speed_10m&timezone=Asia/Taipei&forecast_days=2"

try:
    resp = requests.get(API_URL, timeout=15)
    data = resp.json()
    hourly = data["hourly"]
except Exception as e:
    print(f"API 請求失敗: {e}")
    exit(1)

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

# 找到當前時間的 index
now = datetime.now()
current_hour = now.hour
time_list = hourly["time"]
start_idx = None
for i, t in enumerate(time_list):
    if t.startswith(now.strftime("%Y-%m-%d")) and int(t[11:13]) == current_hour:
        start_idx = i
        break
if start_idx is None:
    start_idx = 0

# 未來 24 小時
end_idx = start_idx + 24
times = hourly["time"][start_idx:end_idx]
temps = hourly["temperature_2m"][start_idx:end_idx]
feels = hourly["apparent_temperature"][start_idx:end_idx]
humids = hourly["relative_humidity_2m"][start_idx:end_idx]
rains = hourly["precipitation_probability"][start_idx:end_idx]
codes = hourly["weather_code"][start_idx:end_idx]
winds = hourly["wind_speed_10m"][start_idx:end_idx]

# === 風速警示檢查 ===
wind_alerts = []
for i, w in enumerate(winds):
    if w > WIND_ALERT_THRESHOLD:
        hour = times[i][11:16]
        wind_alerts.append(f"  ⚠️ {hour} — {w} km/h")

# 發送風速警示（如果有）
if wind_alerts:
    alert_msg = f"""🚨 <b>風速過強警示</b>

📍 地點：雲林縣水林鄉
🌬️ 警示標準：> {WIND_ALERT_THRESHOLD} km/h

{chr(10).join(wind_alerts)}

⚠️ 請注意：
• 太陽能面板可能受強風影響
• 建議檢查支架穩固性
• 午後時段風力最強，請留意"""
    send_telegram_alert(alert_msg)
    print(f"風速警示已發送！共 {len(wind_alerts)} 次")
else:
    print("風速正常，無需警示")

# 當前風速（用於報告）
cur_wind = winds[0] if winds else 0
cur_wind_alert = " ⚠️" if cur_wind > WIND_ALERT_THRESHOLD else ""

# 日期
date_str = now.strftime("%Y/%m/%d")

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
.wind-alert {{ background: #fff3cd; border: 2px solid #ffc107; border-radius: 10px; padding: 12px; margin-bottom: 16px; text-align: center; color: #856404; font-weight: bold; }}
table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; }}
th {{ background: #1a3a5c; color: white; padding: 10px; text-align: center; }}
td {{ padding: 8px; text-align: center; border-bottom: 1px solid #eee; }}
tr:nth-child(even) {{ background: #f8fafc; }}
tr:hover {{ background: #e8f0fa; }}
.section-title {{ color: #1a3a5c; border-left: 4px solid #4a90d9; padding-left: 12px; margin: 20px 0 12px; }}
.rain-high {{ color: #e74c3c; font-weight: bold; }}
.rain-mid {{ color: #f39c12; }}
.rain-low {{ color: #27ae60; }}
.wind-high {{ color: #e74c3c; font-weight: bold; }}
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
  <div class="big-temp">{temps[0]}°C</div>
  <div>
    <div class="big-desc">{get_desc(codes[0])}</div>
    <div style="font-size:14px;opacity:0.85;margin-top:4px;">體感溫度 {feels[0]}°C</div>
  </div>
</div>

<div class="info-grid">
  <div class="info-item"><div class="info-label">🌡️ 體感溫度</div><div class="info-val">{feels[0]}°C</div></div>
  <div class="info-item"><div class="info-label">💧 濕度</div><div class="info-val">{humids[0]}%</div></div>
  <div class="info-item"><div class="info-label">🌧️ 降雨機率</div><div class="info-val">{rains[0]}%</div></div>
  <div class="info-item"><div class="info-label">🌬️ 風速</div><div class="info-val">{cur_wind} km/h</div></div>
</div>
"""

# 如果有風速警示，加入警示框
if wind_alerts:
    html += f'<div class="wind-alert">🚨 風速過強警示：未來24小時內有 {len(wind_alerts)} 次風速超過 {WIND_ALERT_THRESHOLD} km/h</div>'

html += f"""
<div class="section-title">⏰ 未來24小時每小時預報</div>
<table>
<tr><th>時間</th><th>天氣</th><th>溫度</th><th>體感</th><th>濕度</th><th>降雨機率</th><th>風速</th></tr>
"""

for i in range(len(times)):
    t = times[i]
    hour = t[11:16]
    rain_class = "rain-high" if rains[i] >= 60 else ("rain-mid" if rains[i] >= 30 else "rain-low")
    wind_class = "wind-high" if winds[i] > WIND_ALERT_THRESHOLD else ""
    html += f"<tr><td>{hour}</td><td>{get_desc(codes[i])}</td><td>{temps[i]}°C</td><td>{feels[i]}°C</td><td>{humids[i]}%</td><td class='{rain_class}'>{rains[i]}%</td><td class='{wind_class}'>{winds[i]} km/h</td></tr>"

html += """
</table>

<div class="section-title">👗 穿著建議</div>
<div class="tips">
<ul>
<li>🩴 上午炎熱潮濕，建議穿著輕薄透氣衣物，攜帶防曬用品</li>
<li>🌧️ 下午時段降雨機率較高，建議出門攜帶雨具</li>
<li>💧 高濕度環境（85%以上），注意防潮防霉</li>
<li>🌬️ 午後風力增強，戶外活動注意安全</li>
</ul>
</div>

<div class="footer">資料來源：Open-Meteo API｜生成時間：""" + now.strftime("%Y-%m-%d %H:%M") + """</div>
</div>
</body>
</html>
"""

output_path = f"/home/jhe/.openclaw/workspace/weather/weather_{now.strftime('%Y-%m-%d')}.html"
with open(output_path, "w") as f:
    f.write(html)
print(f"HTML generated: {output_path}")
print(f"Wind alert count: {len(wind_alerts)}")
