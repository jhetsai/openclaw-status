#!/usr/bin/env python3
"""
太陽能發電記錄流程
用法:
  python3 solar_log.py [累計kWh] [天氣]   # 新增記錄
  python3 solar_log.py --fill-gaps         # 自動掃描並補漏
  python3 solar_log.py --check-gaps        # 只掃描不補

範例:
  python3 solar_log.py 267.5
  python3 solar_log.py 267.5 晴
"""

import sys
import csv
import subprocess
import json
import urllib.request
from datetime import datetime, date, timedelta
from pathlib import Path

CSV_FILE = '/home/jhe/.openclaw/workspace/solar_history.csv'

# 雲林水林座標
LAT = 23.55
LON = 120.16


def get_weather():
    """從 wttr.in 取得水林天氣（用座標避免 geocode 到大陸同名地名）"""
    try:
        result = subprocess.run(
            ['curl', '-s', 'wttr.in/23.55,120.16?format=j1'],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(result.stdout)
        c = data['current_condition'][0]
        return {
            'weather': c['weatherDesc'][0]['value'],
            'uv': int(c['uvIndex']),
            'wind': float(c['windspeedKmph']),
            'temp': float(c['temp_C'])
        }
    except:
        return {'weather': '未知', 'uv': 0, 'wind': 0, 'temp': 0}


def fetch_openmeteo_current():
    """從 Open-Meteo 取得水林即時天氣（拿來驗證 wttr.in）"""
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=23.55&longitude=120.16&current=temperature_2m,wind_speed_10m,cloud_cover,weather_code&timezone=Asia%2FTaipei"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())['current']
        return {
            'temp': float(d['temperature_2m']),
            'wind': float(d['wind_speed_10m']),
            'cloud': float(d['cloud_cover']),
            'code': int(d['weather_code'])
        }
    except Exception as e:
        return None


def validate_weather(wttr_weather):
    """驗證 wttr.in 天氣是否合理。差距> 5°C 警告"""
    om = fetch_openmeteo_current()
    if not om:
        return wttr_weather, '⚠️ Open-Meteo 抓不到，跳過驗證'
    
    diff = wttr_weather['temp'] - om['temp']
    if abs(diff) > 5:
        return om, f'⚠️ 氣溫與 Open-Meteo 差 {diff:+.1f}°C，自動採用 Open-Meteo 值'
    return wttr_weather, f'✅ 驗證通過（差距 {diff:+.1f}°C）'


def fetch_historical_weather(date_str):
    """從 Open-Meteo 取得歷史天氣"""
    try:
        url = f"https://archive-api.open-meteo.com/v1/archive?latitude={LAT}&longitude={LON}&start_date={date_str}&end_date={date_str}&daily=cloud_cover_mean,shortwave_radiation_sum,temperature_2m_mean,precipitation_sum&timezone=Asia%2FTaipei"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        d = data['daily']
        return {
            'cloud': d['cloud_cover_mean'][0],
            'radiation': d['shortwave_radiation_sum'][0],
            'temp': d['temperature_2m_mean'][0],
            'precip': d['precipitation_sum'][0]
        }
    except Exception as e:
        return None


def read_all_entries():
    """讀取 CSV 全部資料（傳回 list of list）"""
    entries = []
    with open(CSV_FILE, 'r') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if row and row[0]:
                entries.append(row)
    return entries


def read_last_entry():
    """讀取 CSV 最後一筆資料（傳回 dict）"""
    entries = read_all_entries()
    if not entries:
        return None
    with open(CSV_FILE, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows[-1] if rows else None


def write_entry(date_str, total_kwh, daily_kwh, weather_info, note=''):
    """寫入新資料到 CSV"""
    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            date_str,
            f'{total_kwh:.1f}',
            f'{daily_kwh:.1f}',
            weather_info['weather'],
            weather_info['uv'],
            weather_info['wind'],
            weather_info['temp'],
            note
        ])


def insert_entry(entries, idx, date_str, total_kwh, daily_kwh, weather_info, note=''):
    """在指定位置插入新資料"""
    new_row = [
        date_str,
        f'{total_kwh:.1f}',
        f'{daily_kwh:.1f}',
        weather_info['weather'],
        str(weather_info['uv']),
        str(weather_info['wind']),
        str(weather_info['temp']),
        note
    ]
    entries.insert(idx, new_row)
    return entries


def write_all(entries):
    """重寫整個 CSV"""
    fieldnames = ['日期', '累計kWh', '日發電kWh', '天氣', 'UV指數', '風速km/h', '氣溫°C', '備註']
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames)
        for row in entries:
            # 補齊欄位
            while len(row) < len(fieldnames):
                row.append('')
            writer.writerow(row[:len(fieldnames)])


def find_gaps(entries):
    """找出所有缺漏的日期"""
    gaps = []
    for i in range(len(entries) - 1):
        d1 = datetime.strptime(entries[i][0], '%Y-%m-%d')
        d2 = datetime.strptime(entries[i+1][0], '%Y-%m-%d')
        gap_days = (d2 - d1).days
        if gap_days > 1:
            for j in range(1, gap_days):
                missing_date = (d1 + timedelta(days=j)).strftime('%Y-%m-%d')
                gaps.append({
                    'date': missing_date,
                    'prev_date': entries[i][0],
                    'prev_cum': float(entries[i][1]),
                    'next_date': entries[i+1][0],
                    'next_cum': float(entries[i+1][1])
                })
    return gaps


def estimate_daily_generation(target_date, prev_date, prev_cum, next_date, next_cum, entries):
    """用歷史天氣 + 相似日推算"""
    # 1. 抓目標日天氣
    target_weather = fetch_historical_weather(target_date)
    if not target_weather:
        return None, None

    # 2. 找 CSV 中相似天氣的日（雲量±15%, 氣溫±3°C）
    similar_days = []
    for entry in entries:
        if entry == entries[0] or entry == entries[-1]:
            continue
        try:
            entry_cloud = float(entry[4]) if entry[4] else 50  # UV 暫當雲量代理
            entry_temp = float(entry[6]) if entry[6] else 25
        except:
            continue
        # 簡化：用 UV index 與氣溫當相似度（無法直接得雲量）
        # 改用「氣溫相近」+「無降雨」當相似
        if abs(entry_temp - target_weather['temp']) <= 3:
            try:
                daily = float(entry[2])
                similar_days.append((entry[0], daily, entry_temp))
            except:
                pass

    # 3. 加權平均
    if similar_days:
        # 簡化：直接平均
        avg_daily = sum(d[1] for d in similar_days) / len(similar_days)
    else:
        # 沒相似日 → 用差距平均
        total_days = (datetime.strptime(next_date, '%Y-%m-%d') - datetime.strptime(prev_date, '%Y-%m-%d')).days
        avg_daily = round((next_cum - prev_cum) / total_days, 2)

    # 4. 累計值
    new_cum = round(prev_cum + avg_daily, 2)
    return new_cum, round(avg_daily, 2)


def fill_gaps(dry_run=False):
    """掃描並補所有漏失日"""
    entries = read_all_entries()
    gaps = find_gaps(entries)
    
    if not gaps:
        print("✅ 沒有缺漏日期！")
        return
    
    print(f"🔍 找到 {len(gaps)} 個缺漏日：\n")
    for g in gaps:
        print(f"  缺: {g['date']}  (前: {g['prev_date']} = {g['prev_cum']}, 後: {g['next_date']} = {g['next_cum']})")
    
    if dry_run:
        print("\n(dry-run 模式，未實際寫入)")
        return
    
    print("\n開始補...\n")
    filled_count = 0
    for g in gaps:
        prev = float(g['prev_cum'])
        new_cum, daily = estimate_daily_generation(
            g['date'], g['prev_date'], prev, g['next_date'], g['next_cum'], entries
        )
        if new_cum is None:
            print(f"  ❌ {g['date']}: 抓不到天氣，跳過")
            continue
        
        weather = fetch_historical_weather(g['date'])
        weather_info = {
            'weather': f"雲量 {weather['cloud']}% (估)",
            'uv': 0,
            'wind': 0,
            'temp': weather['temp']
        }
        note = f"⚠️ 自動填補 (Open-Meteo 估, 雲 {weather['cloud']}%, 輻射 {weather['radiation']:.1f} MJ/m²)"
        
        # 找插入位置
        for i, row in enumerate(entries):
            if row[0] == g['prev_date']:
                insert_entry(entries, i + 1, g['date'], new_cum, daily, weather_info, note)
                filled_count += 1
                print(f"  ✅ {g['date']}: 累計 {new_cum} kWh, 日發電 {daily} kWh (雲量 {weather['cloud']}%, 氣溫 {weather['temp']}°C)")
                break
    
    # 寫回
    write_all(entries)
    print(f"\n🎉 完成！共補上 {filled_count} 個缺漏日。")


def main():
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python3 solar_log.py <累計kWh> [天氣]")
        print("  python3 solar_log.py --fill-gaps")
        print("  python3 solar_log.py --check-gaps")
        sys.exit(1)
    
    # 自動補漏模式
    if sys.argv[1] == '--fill-gaps':
        fill_gaps(dry_run=False)
        return
    if sys.argv[1] == '--check-gaps':
        fill_gaps(dry_run=True)
        return
    
    # 正常新增模式
    total_kwh = float(sys.argv[1])
    user_weather = sys.argv[2] if len(sys.argv) > 2 else None

    weather = get_weather()
    if user_weather:
        weather['weather'] = user_weather

    # 自動驗證是否被 wttr.in geocode 帶錯
    weather, validation_msg = validate_weather(weather)
    print(f"🔍 驗證：{validation_msg}")

    last = read_last_entry()
    if last:
        prev_kwh = float(last['累計kWh'])
        daily_kwh = round(total_kwh - prev_kwh, 1)
        print(f"📊 上筆記錄：{last['日期']} → {prev_kwh} kWh")
    else:
        prev_kwh = 0
        daily_kwh = total_kwh
        print("📊 首次記錄")

    today = date.today().strftime('%Y-%m-%d')
    write_entry(today, total_kwh, daily_kwh, weather)

    print(f"""
✅ 已記錄：{today}
━━━━━━━━━━━━━━━━━━
📈 累積發電：{total_kwh} kWh
⚡ 日發電量：{daily_kwh} kWh
🌤️ 天氣：{weather['weather']}
☀️ UV指數：{weather['uv']}
💨 風速：{weather['wind']} km/h
🌡️ 氣溫：{weather['temp']}°C
━━━━━━━━━━━━━━━━━━
""")
    
    # 新增後自動檢查漏失
    print("\n🔍 自動檢查漏失日...")
    fill_gaps(dry_run=True)


if __name__ == '__main__':
    main()
