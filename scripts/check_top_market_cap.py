#!/usr/bin/env python3
"""
市值/股價 查詢驗證腳本
用途：確保市值前十排名等問題，先通过API查詢才能回答
"""
import sys, json, subprocess

def get_market_cap(symbol):
    """從 Yahoo Finance 取得即時市值"""
    try:
        cmd = f'/tmp/venv/bin/python3 -c "import yfinance as yf; t=yf.Ticker(\'{symbol}\'); i=t.info; print(json.dumps({{\\"price\\": i.get(\\"currentPrice\\",0), \\"mktcap\\": i.get(\"marketCap\\",0)}}))"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            data = json.loads(result.stdout.strip())
            return data.get('mktcap', 0), data.get('price', 0)
    except:
        pass
    return 0, 0

def get_top_market_cap(limit=10):
    """取得全球市值前十（使用已知主要股票名單 + 動態擴展）"""
    # 主要候選股票（覆蓋全球最大市值的候選名單）
    candidates = {
        'NVDA': 'NVIDIA', 'AAPL': 'Apple', 'GOOGL': 'Alphabet',
        'MSFT': 'Microsoft', 'AMZN': 'Amazon', 'META': 'Meta',
        'TSLA': 'Tesla', 'TSM': 'TSMC', 'BRK-A': 'Berkshire',
        'JPM': 'JPMorgan', 'V': 'Visa', 'WMT': 'Walmart',
        'UNH': 'UnitedHealth', 'LLY': 'Eli Lilly', 'XOM': 'Exxon',
        'MA': 'Mastercard', 'AVGO': 'Broadcom', 'ASML': 'ASML',
        'NVO': 'Novo Nordisk', 'ARAMCO': 'Saudi Aramco',
        'HD': 'Home Depot', 'CVX': 'Chevron', 'MRK': 'Merck',
        'ABBV': 'AbbVie', 'KO': 'Coca-Cola', 'PEP': 'PepsiCo',
        'COST': 'Costco', 'TMO': 'Thermo Fisher', 'MCD': 'McDonalds',
        'CSCO': 'Cisco', 'ACN': 'Accenture', 'ABT': 'Abbott',
    }
    
    results = []
    for sym, name in candidates.items():
        mktcap, price = get_market_cap(sym)
        if mktcap and mktcap > 0:
            results.append({'symbol': sym, 'name': name, 'mktcap': mktcap, 'price': price})
    
    # 排序
    results.sort(key=lambda x: x['mktcap'], reverse=True)
    return results[:limit]

if __name__ == '__main__':
    print("=== 全球市值前十即時查詢 ===")
    print(f"時間: {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()}")
    print("-" * 60)
    
    top10 = get_top_market_cap(10)
    for i, r in enumerate(top10, 1):
        print(f"{i:>2}. {r['name']:<20} ({r['symbol']:<6}) ${r['price']:>10.2f}  ${r['mktcap']/1e12:>6.2f}T")
    
    print()
    print("⚠️  此資料僅供參考，請以 TradingView 等專業平台為準")