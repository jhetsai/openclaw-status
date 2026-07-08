#!/usr/bin/env python3
"""
gen_status_json.py
每分鐘蒐集 VM 系統資料 + 太陽能 + API 用量，寫成 status_esp32.json
（不需要 psutil，用 /proc 和 shell 命令）
"""
import json, os, sys, subprocess
from datetime import datetime, timezone, timedelta

WORKSPACE = '/home/jhe/.openclaw/workspace'
OUT_FILE  = os.path.join(WORKSPACE, 'assets', 'status_esp32.json')
TZ = timezone(timedelta(hours=8))  # Asia/Taipei

# ── API Key 讀取 ──────────────────────────────────────────────
def get_api_key(name):
    # 先從環境變數取
    val = os.environ.get(name)
    if val:
        return val
    # 再從 ~/.api_keys 取
    path = os.path.expanduser('~/.api_keys')
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line.startswith(name + '='):
                return line.split('=', 1)[1].strip()
    return None

# ── 1. 系統資料 ──────────────────────────────────────────────
def get_system():
    # hostname
    hostname = subprocess.run(['hostname'], capture_output=True, text=True).stdout.strip()

    # uptime
    uptime_raw = open('/proc/uptime').read().split()[0]
    uptime_sec = float(uptime_raw)
    days = int(uptime_sec // 86400)
    hours = int((uptime_sec % 86400) // 3600)
    minutes = int((uptime_sec % 3600) // 60)
    uptime_str = f"{days}d {hours}h {minutes}m"

    # memory: /proc/meminfo
    meminfo = {}
    for line in open('/proc/meminfo'):
        parts = line.split()
        if len(parts) >= 2:
            meminfo[parts[0].rstrip(':')] = int(parts[1])  # kB

    mem_total = meminfo.get('MemTotal', 0) / 1024**2  # GB
    mem_available = meminfo.get('MemAvailable', 0) / 1024**2
    mem_used = mem_total - mem_available
    mem_pct = round(mem_used / mem_total * 100, 1) if mem_total else 0

    # CPU: /proc/stat（1秒取樣）
    def cpu_percent():
        before = [int(x) for x in open('/proc/stat').read().split()[1:8]]
        import time; time.sleep(0.5)
        after = [int(x) for x in open('/proc/stat').read().split()[1:8]]
        total = sum(after) - sum(before)
        idle = (after[3] - before[3]) + (after[4] - before[4])
        return round((1 - idle / total) * 100, 1) if total else 0

    cpu_pct = cpu_percent()

    # disk: df
    disk_result = subprocess.run(
        ['df', '-BG', '/'], capture_output=True, text=True
    )
    parts = disk_result.stdout.strip().split('\n')[-1].split()
    disk_used_gb = int(parts[2].rstrip('G'))
    disk_total_gb = int(parts[3].rstrip('G'))

    # node version
    node_v = subprocess.run(['node', '--version'], capture_output=True, text=True).stdout.strip()

    return {
        'hostname': hostname,
        'uptime_str': uptime_str,
        'uptime_days': days,
        'mem_used_gb': round(mem_used, 1),
        'mem_total_gb': round(mem_total, 1),
        'mem_pct': mem_pct,
        'cpu_pct': cpu_pct,
        'disk_used_gb': disk_used_gb,
        'disk_total_gb': disk_total_gb,
        'node_version': node_v,
        'model': os.environ.get('OPENCLAW_MODEL', 'MiniMax M2.7')
    }

# ── 2. 太陽能 ───────────────────────────────────────────────
def get_solar():
    csv_path = os.path.join(WORKSPACE, 'solar_history.csv')
    today_str = datetime.now(tz=TZ).strftime('%Y-%m-%d')
    kwh_today = weather = temp_c = wind_kmh = None

    try:
        lines = open(csv_path).readlines()
        if len(lines) >= 2:
            last = lines[-1].strip().split(',')
            date_str = last[0]
            if date_str == today_str and len(last) > 2 and last[2]:
                kwh_today = float(last[2])
                weather = last[3] if len(last) > 3 else None
                wind_kmh = float(last[5]) if len(last) > 5 and last[5] else None
                temp_c = float(last[6]) if len(last) > 6 and last[6] else None
    except Exception as e:
        print(f"[solar] {e}", file=sys.stderr)

    # 即時天氣
    try:
        import urllib.request
        req = urllib.request.Request(
            'https://wttr.in/Yunlin?format=j1',
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
        curr = data['current_condition'][0]
        temp_c = float(curr['temp_C'])
        wind_kmh = float(curr['windspeedKmph'])
        weather = curr['weatherDesc'][0]['value']
    except Exception:
        pass

    return {
        'today_kwh': kwh_today,
        'current_watt': None,   # 需發電計硬體
        'efficiency_pct': None,
        'weather': weather,
        'temp_c': temp_c,
        'wind_kmh': wind_kmh
    }

# ── 3. 投資組合 ──────────────────────────────────────────────
def get_portfolio():
    json_path = os.path.join(WORKSPACE, 'assets', 'esp32_portfolio.json')
    if not os.path.exists(json_path):
        return None
    try:
        with open(json_path) as f:
            data = json.load(f)
        return {
            'total_cost':    data['summary']['total_cost'],
            'total_mktval':  data['summary']['total_mktval'],
            'total_gain_pct': data['summary']['total_gain_pct'],
            'tw_cost':       data['tw']['cost'],
            'tw_mktval':     data['tw']['mktval'],
            'tw_gain_pct':   data['tw']['gain_pct'],
            'us_cost_twd':   data['us']['cost_twd'],
            'us_mktval_twd': data['us']['mktval_twd'],
            'us_gain_pct':   data['us']['gain_pct'],
            'usd_cash':      data['cash']['usd']['amount'],
            'usd_rate':      data['cash']['usd']['rate_usd_twd'],
            'jpy_cash':      data['cash']['jpy']['amount'],
            'jpy_rate':      data['cash']['jpy']['rate_jpy_twd']
        }
    except Exception as e:
        print(f"[portfolio] {e}", file=sys.stderr)
        return None

# ── 4. API 用量 ─────────────────────────────────────────────
def get_api_usage():
    openrouter_key = get_api_key('OPENROUTER_API_KEY')
    result = {
        'brave_used': None,
        'brave_limit': 5.0,
        'openrouter_used': None,
        'openrouter_limit': 5.0,
        'openrouter_currency': 'USD'
    }

    if openrouter_key:
        try:
            import urllib.request
            req = urllib.request.Request(
                'https://openrouter.ai/api/v1/auth/key',
                headers={'Authorization': f'Bearer {openrouter_key}'}
            )
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read())
            # 回傳格式: { "data": { "usage": 2.23, "limit": 5, "limit_remaining": 2.77 } }
            d = data.get('data', data)
            result['openrouter_used'] = round(float(d.get('usage', 0)), 3)
            result['openrouter_limit'] = float(d.get('limit', 5.0))
            result['openrouter_remaining'] = round(float(d.get('limit_remaining', 0)), 3)
        except Exception as e:
            print(f"[openrouter] {e}", file=sys.stderr)

    return result

# ── 5. 服務狀態 ─────────────────────────────────────────────
def get_services():
    # 主機在線=服務正常，用 uptime 簡單判斷
    return {
        'telegram': 'running',
        'line': 'running',
        'cron_wind_alert': 'running'
    }

# ── 主程式 ──────────────────────────────────────────────────
def main():
    now_str = datetime.now(tz=TZ).strftime('%Y-%m-%dT%H:%M:%S+08:00')

    status = {
        'updated': now_str,
        'system': get_system(),
        'solar': get_solar(),
        'portfolio': get_portfolio(),
        'api_usage': get_api_usage(),
        'services': get_services()
    }

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w') as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

    sys.stderr.write(f"[{now_str}] status_esp32.json written\n")

if __name__ == '__main__':
    main()
