#!/usr/bin/env python3
"""
ETL script: Stock data to Vector Database
Reads portfolio_data.json, dividend_data.json, etc. and stores in pgvector
"""

import os
import json
import psycopg2
from sentence_transformers import SentenceTransformer
from datetime import datetime

# Config
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'dbname': 'openclaw',
    'user': 'jhe',
    'password': 'openclaw_secure_pass_2026'
}

ASSETS_DIR = '/home/jhe/.openclaw/workspace/assets'
US_STOCK_DIR = '/home/jhe/.openclaw/workspace/us_stock'
MODEL_NAME = 'all-MiniLM-L6-v2'

def format_portfolio(data):
    """Convert portfolio_data.json to text chunks"""
    chunks = []
    
    fx = data.get('fx', {})
    stocks_dict = data.get('stocks', {})  # {'tw': [...], 'us': [...]}
    
    # Summary
    summary = f"""股票投資組合總覽
更新時間：{data.get('updated', 'N/A')}
美金匯率：{fx.get('USD_TWD', 'N/A')} TWD/USD

"""
    chunks.append(('portfolio_summary', '股票總覽', summary.strip()))
    
    # Taiwan stocks
    tw_stocks = stocks_dict.get('tw', [])
    if tw_stocks:
        tw_text = "台股持股\n"
        for s in tw_stocks:
            tw_text += f"""股票：{s.get('name', '')}（{s.get('symbol', '')}）
持股：{s.get('shares', 0)} 股
成本均價：{s.get('cost', 0)} 元
現價：{s.get('price', 0)} 元
總成本：{s.get('totalCost', s.get('total_cost', 0))} 元
市值：{s.get('mktval', s.get('market_value', 0))} 元
帳面獲利：{s.get('gain', 0)} 元（{s.get('retPct', s.get('gain_pct', 0))}%）
殖利率：{s.get('divYield', 'N/A')}%
年化配息：{s.get('annDiv', 'N/A')} 元
配息頻率：{s.get('freq', 'N/A')}

"""
        chunks.append(('tw_stocks', '台股', tw_text.strip()))
    
    # US stocks
    us_stocks = stocks_dict.get('us', [])
    if us_stocks:
        us_text = "美股持股\n"
        for s in us_stocks:
            us_text += f"""股票：{s.get('name', '')}（{s.get('symbol', '')}）
持股：{s.get('shares', 0)} 股
成本均價：{s.get('cost', 0)} USD
現價：{s.get('price', 0)} USD
總成本：{s.get('costTwd', 0)} TWD
市值：{s.get('mktvalTwd', 0)} TWD
帳面獲利：{s.get('gain', 0)} TWD（{s.get('retPct', 0)}%）
殖利率：{s.get('divYield', 'N/A')}%
季配息：{s.get('div', 0)} USD
年化配息：{s.get('annDivTwd', 'N/A')} TWD

"""
        chunks.append(('us_stocks', '美股', us_text.strip()))
    
    # Dividends - TW confirmed
    divs = data.get('dividends', {})
    tw_div = divs.get('tw', {})
    tw_confirmed = tw_div.get('confirmed', {}).get('rows', [])
    if tw_confirmed:
        div_text = "台股配息歷史（已入帳）\n"
        for r in tw_confirmed:
            div_text += f"{r.get('ex_date', '')} {r.get('code', '')} 配 {r.get('cash', '')} 元（{r.get('shares', 0)}股）領 {r.get('amount', 0)} 元\n"
        chunks.append(('tw_dividend_confirmed', '台股配息', div_text.strip()))
    
    # Dividends - TW pending
    tw_pending = tw_div.get('pending', {}).get('rows', [])
    if tw_pending:
        div_text = "台股配息（待發放）\n"
        for r in tw_pending:
            div_text += f"{r.get('ex_date', '')} {r.get('code', '')} 配 {r.get('cash', '')} 元（{r.get('shares', 0)}股）領 {r.get('amount', 0)} 元，發放日 {r.get('payout', '')}\n"
        chunks.append(('tw_dividend_pending', '台股配息', div_text.strip()))
    
    return chunks

def format_div_history(data):
    """Convert div_history.json to text chunks"""
    chunks = []
    
    by_stock = data.get('by_stock', {})
    for symbol, stock_data in by_stock.items():
        if not isinstance(stock_data, dict):
            continue
        years = stock_data.get('years', {})
        text = f"美股配息記錄 - {symbol}\n"
        for year, records in sorted(years.items(), reverse=True)[:3]:  # Last 3 years
            if not isinstance(records, list):
                continue
            text += f"{year}年："
            for r in records:
                text += f"{r.get('date', '')} {r.get('per_share', '')}USD "
            text += "\n"
        chunks.append((symbol, symbol, text.strip()))
    
    return chunks

def main():
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Starting stock ETL...')
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Loading embedding model...')
    model = SentenceTransformer(MODEL_NAME)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Model loaded: {model.device}')
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    cur.execute('TRUNCATE TABLE stock_chunks RESTART IDENTITY;')
    conn.commit()
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Cleared existing stock chunks')
    
    total_chunks = 0
    
    # Process portfolio_data.json
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Processing portfolio_data.json...')
    pf_path = os.path.join(ASSETS_DIR, 'portfolio_data.json')
    if os.path.exists(pf_path):
        with open(pf_path, 'r', encoding='utf-8') as f:
            pf_data = json.load(f)
        chunks = format_portfolio(pf_data)
        for code, name, text in chunks:
            emb = model.encode([text])[0]
            cur.execute("""
                INSERT INTO stock_chunks (stock_code, stock_name, category, chunk_text, embedding)
                VALUES (%s, %s, %s, %s, %s)
            """, (code, name, 'portfolio', text, emb.tolist()))
        total_chunks += len(chunks)
        print(f'  Added {len(chunks)} portfolio chunks')
    
    # Process div_history.json
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Processing div_history.json...')
    dh_path = os.path.join(US_STOCK_DIR, 'div_history.json')
    if os.path.exists(dh_path):
        with open(dh_path, 'r', encoding='utf-8') as f:
            dh_data = json.load(f)
        chunks = format_div_history(dh_data)
        for code, name, text in chunks:
            emb = model.encode([text])[0]
            cur.execute("""
                INSERT INTO stock_chunks (stock_code, stock_name, category, chunk_text, embedding)
                VALUES (%s, %s, %s, %s, %s)
            """, (code, name, 'div_history', text, emb.tolist()))
        total_chunks += len(chunks)
        print(f'  Added {len(chunks)} div_history chunks')
    
    conn.commit()
    
    cur.execute('SELECT COUNT(*) FROM stock_chunks;')
    count = cur.fetchone()[0]
    cur.execute('SELECT category, COUNT(*) FROM stock_chunks GROUP BY category;')
    cat_counts = cur.fetchall()
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] ETL complete!')
    print(f'  Total chunks: {count}')
    for cat, cnt in cat_counts:
        print(f'    {cat}: {cnt}')
    
    conn.close()

if __name__ == '__main__':
    main()