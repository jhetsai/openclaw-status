#!/usr/bin/env python3
"""
R2 weather.json 生成腳本
- 即時觀測：O-A0001-001（水林站 C0K510）
- 預報：用 R2 緩存的 cwa-forecast.json（F-D0047-025 水林鄉）
- 上傳到 tmp/weather.json
"""
import json, boto3, os, urllib.parse, urllib.request, datetime

CREDS = {}
with open(os.path.expanduser("~/.api_keys")) as f:
    for line in f:
        if line.strip() and not line.startswith("#") and "=" in line:
            k, v = line.strip().split("=", 1)
            CREDS[k.strip()] = v.strip()

R2_BUCKET = CREDS.get("R2_BUCKET", "shared-files")
R2_ID = CREDS.get("R2_ACCOUNT_ID", "83de8038b42470b0576833e6d30e926d")

s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{R2_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=CREDS.get("R2_ACCESS_KEY"),
    aws_secret_access_key=CREDS.get("R2_SECRET_KEY"),
)

CWA_KEY = CREDS.get("CWA_API_KEY", "")

# ── Helper ────────────────────────────────────────────────────
def weather_emoji(w):
    w = w or ""
    if "雷" in w: return "⛈️"
    if "雨" in w: return "🌧️"
    if "雲" in w or "陰" in w: return "🌥️"
    if "晴" in w: return "☀️"
    if "霧" in w or "霾" in w: return "🌫️"
    return "🌤️"

def deg_to_dir(d):
    dirs = ["北","北東","東","南東","南","南西","西","北西"]
    if d < 0 or d > 360: return "無風"
    return dirs[int((d + 22.5) / 45) % 8] + "風"

# ── 即時觀測：O-A0001-001 水林站 ──────────────────────────────
def cwa_fetch(endpoint, params=None):
    base = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"
    url = f"{base}/{endpoint}?Authorization={CWA_KEY}&format=JSON"
    if params:
        url += "&" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=8) as resp:
        return json.load(resp)

obs_data = cwa_fetch("O-A0001-001")
shuilin = None
for s in obs_data.get("records", {}).get("Station", []):
    if s.get("StationId") == "C0K510":
        shuilin = s
        break

if not shuilin:
    print("❌ 水林站觀測資料找不到")
    exit(1)

obs_time_str = shuilin["ObsTime"]["DateTime"]
elem = shuilin["WeatherElement"]

obs_temp    = float(elem.get("AirTemperature", 0))
obs_rh      = float(elem.get("RelativeHumidity", 0))
obs_pressure= float(elem.get("AirPressure", 0))
obs_wind_spd= float(elem.get("WindSpeed", 0))
obs_wind_dir_deg = float(elem.get("WindDirection", 0))
obs_wind_kmh = round(obs_wind_spd * 3.6)
obs_wind_dir_ch = deg_to_dir(obs_wind_dir_deg)
obs_time_fmt = obs_time_str[:16]   # "2026-07-11T13:00"

print(f"   即時觀測 {obs_time_str}: {obs_temp}°C {obs_rh}% {obs_pressure}hPa {obs_wind_kmh}km/h {obs_wind_dir_ch}")

# ── 預報：R2 緩存的 cwa-forecast.json（F-D0047-025 水林鄉）─────
try:
    resp = s3.get_object(Bucket=R2_BUCKET, Key="weather-api/cwa-forecast.json")
    cwa = json.loads(resp["Body"].read().decode("utf-8"))
except Exception as e:
    print(f"❌ Cannot fetch R2 cwa-forecast: {e}")
    exit(1)

fc_current = cwa.get("current", {})
fc_daily   = cwa.get("daily", [])[:4]
fc_wx      = fc_current.get("weather", "未知")
fc_feels   = fc_current.get("feels_like_c", obs_temp)

# ── wttr.in 補 UV ─────────────────────────────────────────────
wt_uv = 0
try:
    wt = json.loads(urllib.request.urlopen(
        "https://wttr.in/Yunlin?format=j1", timeout=5).read())
    wt_uv = int(float(wt["current_condition"][0].get("uvIndex", 0)))
except Exception as e:
    print(f"⚠️ wttr.in UV failed: {e}")

# ── 組裝輸出 ──────────────────────────────────────────────────
day_labels = ["今天", "明天", "後天", "大後天"]
forecast_list = []
for i, d in enumerate(fc_daily):
    forecast_list.append({
        "day": day_labels[i] if i < len(day_labels) else d.get("date", ""),
        "weather": d.get("weather", "未知"),
        "emoji": weather_emoji(d.get("weather", "")),
        "high": round(d.get("high", 0)),
        "low": round(d.get("low", 0)),
        "rain_pct": round(d.get("max_precip_3h_pct", 0))
    })

out = {
    # 即時觀測值（來自 O-A0001-001 水林站）
    "temp": round(obs_temp),
    "feels_like": round(fc_feels),
    "desc": fc_wx,
    "humidity": round(obs_rh),
    "wind": obs_wind_kmh,
    "wind_dir": obs_wind_dir_ch,
    "uv": wt_uv,
    "pressure": round(obs_pressure),
    "time": obs_time_str,
    "updated": obs_time_fmt,       # 水林站觀測時間（真正的觀測時間）
    "forecast": forecast_list
}

# 上傳到 R2
body = json.dumps(out, ensure_ascii=False).encode("utf-8")
s3.put_object(Bucket=R2_BUCKET, Key="tmp/weather.json", Body=body,
               ContentType="application/json")
print(f"✅ Uploaded: {out['temp']}°C {out['desc']} | UV={out['uv']} pressure={out['pressure']}hPa wind={out['wind']}km/h {out['wind_dir']}")
for f in out["forecast"]:
    print(f"   {f['day']} {f['emoji']} {f['weather']} {f['low']}–{f['high']}°C 🌧️{f['rain_pct']}%")
