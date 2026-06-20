#!/usr/bin/env python3
"""
us_giants_report.py - US Tech Giants 每週分析報告（發送給 Wu Jack）
排程：VM Cron（週五 10:00）

使用 Finnhub API 取得股價

使用方法：
  python3 us_giants_report.py
"""

import json
import subprocess
import urllib.request
import urllib.error
import os
from datetime import datetime

# ============ 設定 ============
TELEGRAM_BOT_TOKEN = "8793435853:AAHF2snG1sYEpno-O0uvvRyPL52cqdxER8A"
TELEGRAM_CHAT_ID = "7136074624"  # Wu Jack

FINNHUB_KEY = "d7jor7hr01qnk4oca0m0d7jor7hr01qnk4oca0mg"

STOCKS = {
    "AAPL": "蘋果",
    "MSFT": "微軟",
    "GOOGL": "Google",
    "AMZN": "亞馬遜",
    "META": "Meta",
    "TSLA": "特斯拉"
}

WORKSPACE = "/home/jhe/.openclaw/workspace"

# ============ 取得股價 ============
def fetch_finnhub_quote(symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_KEY}"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read())
            return {
                "c": data.get("c", 0),
                "pc": data.get("pc", 0),
                "h": data.get("h", 0),
                "l": data.get("l", 0),
            }
    except Exception as e:
        return None

def get_stock_data():
    result = {}
    for sym, name in STOCKS.items():
        data = fetch_finnhub_quote(sym)
        if data:
            price = data["c"]
            prev = data["pc"]
            chg = price - prev
            chg_pct = (chg / prev * 100) if prev > 0 else 0
            result[sym] = {
                "name": name,
                "price": price,
                "prev": prev,
                "chg": chg,
                "chg_pct": chg_pct,
                "high": data["h"],
                "low": data["l"]
            }
    return result

# ============ 發送 Telegram ============
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status == 200
    except Exception as e:
        print(f"Telegram send error: {e}")
        return False

# ============ 產生報告內容 ============
def generate_report(stocks_data):
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    
    lines = ["📊 *US Tech Giants 每週分析*\n", f"📅 更新時間：{now}\n"]
    lines.append("─" * 40)
    lines.append("| 代號 | 名稱 | 現價 | 漲跌 | 漲% |")
    lines.append("|------|------|------|------|------|")
    
    for sym, data in stocks_data.items():
        arrow = "🔺" if data["chg"] >= 0 else "🔻"
        lines.append(f"| {sym} | {data['name']} | ${data['price']:.2f} | {arrow} ${abs(data['chg']):.2f} | {data['chg_pct']:+.2f}% |")
    
    lines.append("─" * 40)
    lines.append("\n📈 分析重點：")
    lines.append("• 科技股本週表現")
    lines.append("• 法人資金動向")
    lines.append("• 關鍵技術支撐壓力")
    lines.append("• 後市展望")
    
    return "\n".join(lines)

# ============ 主程式 ============
def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] US Tech Giants 報告開始...")
    
    # 1. 取得股價
    print("取得股價資料...")
    stocks = get_stock_data()
    if not stocks:
        print("錯誤：無法取得股價資料")
        return False
    
    # 2. 產生報告
    print("產生分析報告...")
    report = generate_report(stocks)
    
    # 3. 發送到 Telegram
    print("發送到 Telegram...")
    success = send_telegram(report)
    
    if success:
        print("✅ 報告發送成功！")
        return True
    else:
        print("❌ 報告發送失敗")
        return False

if __name__ == "__main__":
    main()