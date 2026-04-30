#!/usr/bin/env python3
"""抓取歷史股價，儲存到 stock_history.json"""
import json, subprocess, os
from datetime import datetime, timedelta

WORKSPACE = "/home/jhe/.openclaw/workspace"
HISTORY_FILE = os.path.join(WORKSPACE, "stock_history.json")

TW_CODES = ["0056", "00692", "00712", "00713", "00717", "00878", "00891", "00940", "009802", "1101", "2886"]
US_CODES = ["AAPL", "MSFT", "BND"]

def fetch_yahoo_history(symbol, market="TW", days=30):
    suffix = ".TW" if market == "TW" else ""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}{suffix}?interval=1d&range={days}d"
    try:
        result = subprocess.run(
            ['curl', '-4', '-s', '--max-time', '10', '-H', 'User-Agent: Mozilla/5.0', url],
            capture_output=True, text=True, timeout=12
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            result_data = data.get("chart", {}).get("result")
            if result_data:
                timestamps = result_data[0].get("timestamp", [])
                closes = result_data[0].get("indicators", {}).get("quote", [{}])[0].get("close", [])
                history = []
                for i, (ts, close) in enumerate(zip(timestamps, closes)):
                    if close:
                        date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                        history.append({"date": date, "price": round(close, 2)})
                return history[-days:]
        return []
    except Exception as e:
        print(f"  Warning: {symbol} history error: {e}")
        return []

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return {"tw": {}, "us": {}, "updated": ""}

def save_history(history):
    history["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    print(f"  歷史資料已儲存到 {HISTORY_FILE}")

# Main
print("📊 抓取歷史股價...")
history = load_history()

print("  抓取台股歷史...")
for code in TW_CODES:
    print(f"    {code}...", end=" ", flush=True)
    h = fetch_yahoo_history(code, "TW", 30)
    if h:
        history["tw"][code] = h
        print(f"{len(h)} 筆")
    else:
        print("失敗")

print("  抓取美股歷史...")
for code in US_CODES:
    print(f"    {code}...", end=" ", flush=True)
    h = fetch_yahoo_history(code, "US", 30)
    if h:
        history["us"][code] = h
        print(f"{len(h)} 筆")
    else:
        print("失敗")

save_history(history)
print("✅ 完成！")
