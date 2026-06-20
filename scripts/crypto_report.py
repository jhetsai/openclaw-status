#!/usr/bin/env python3
"""
crypto_report.py - Crypto 每週分析報告（發送給 Wu Jack）
排程：VM Cron（週三、週六 10:00）

主要幣種：BTC、ETH、ADA、SOL、BNB、XRP

使用方法：
  python3 crypto_report.py
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

COINGECKO_API = "https://api.coingecko.com/api/v3"

CRYPTO = {
    "bitcoin": "BTC 比特幣",
    "ethereum": "ETH 以太幣",
    "cardano": "ADA 艾達幣",
    "solana": "SOL",
    "binancecoin": "BNB",
    "ripple": "XRP"
}

WORKSPACE = "/home/jhe/.openclaw/workspace"

# ============ 取得幣價 ============
def fetch_crypto_prices():
    ids = ",".join(CRYPTO.keys())
    url = f"{COINGECKO_API}/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"CoinGecko error: {e}")
        return None

def get_crypto_data():
    data = fetch_crypto_prices()
    if not data:
        return {}
    
    result = {}
    for coin_id, name in CRYPTO.items():
        if coin_id in data:
            price = data[coin_id].get("usd", 0)
            change_24h = data[coin_id].get("usd_24h_change", 0)
            result[coin_id] = {
                "name": name,
                "price": price,
                "change_24h": change_24h
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
def generate_report(crypto_data):
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    
    lines = ["📊 *Crypto 每週市場分析*\n", f"📅 更新時間：{now}\n"]
    lines.append("─" * 40)
    lines.append("| 幣種 | 價格 (USD) | 24h 漲跌 |")
    lines.append("|------|-----------|----------|")
    
    for coin_id, data in crypto_data.items():
        arrow = "🔺" if data["change_24h"] >= 0 else "🔻"
        change_str = f"{arrow} {abs(data['change_24h']):.2f}%"
        lines.append(f"| {data['name']} | ${data['price']:,.0f} | {change_str} |")
    
    lines.append("─" * 40)
    lines.append("\n📈 分析重點：")
    lines.append("• 比特幣維持高波動")
    lines.append("• 以太坊網路升級進展")
    lines.append("• 機構持續買入比特幣")
    lines.append("• 監管動態影響市場情緒")
    
    return "\n".join(lines)

# ============ 主程式 ============
def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Crypto 分析報告開始...")
    
    # 1. 取得幣價
    print("取得加密幣價格...")
    crypto = get_crypto_data()
    if not crypto:
        print("錯誤：無法取得幣價資料")
        return False
    
    # 2. 產生報告
    print("產生分析報告...")
    report = generate_report(crypto)
    
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