#!/usr/bin/env python3
"""
SQL Migration: JSON → PostgreSQL
移轉高優先、中優先資料到 SQL 資料庫
"""

import json
import psycopg2
from datetime import datetime
from pathlib import Path

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'user': 'jhe',
    'password': 'openclaw_secure_pass_2026',
    'database': 'openclaw'
}

WORKSPACE = Path('/home/jhe/.openclaw/workspace')

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

def init_tables(conn):
    """建立所有必要的表格"""
    cur = conn.cursor()
    
    # 1. 台股配息資料
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tw_dividend (
            id SERIAL PRIMARY KEY,
            code VARCHAR(10) NOT NULL,
            period VARCHAR(20) NOT NULL,
            cash_per_share DECIMAL(10,4),
            shares INTEGER,
            amount_twd DECIMAL(12,2),
            ex_date DATE,
            payout DATE,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(code, period, ex_date)
        )
    """)
    
    # 2. 持股組合（台股+美股）
    cur.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_holdings (
            id SERIAL PRIMARY KEY,
            market VARCHAR(5) NOT NULL,  -- 'TW' or 'US'
            symbol VARCHAR(20) NOT NULL,
            name VARCHAR(100),
            shares INTEGER,
            cost DECIMAL(12,4),
            price DECIMAL(12,4),
            market_value DECIMAL(14,2),
            gain DECIMAL(14,2),
            gain_pct DECIMAL(8,2),
            div DECIMAL(8,4),
            ann_div DECIMAL(12,2),
            div_yield DECIMAL(6,2),
            div_yield_cost DECIMAL(6,2),
            sector VARCHAR(50),
            update_time TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(market, symbol)
        )
    """)
    
    # 3. 庫存商品（神腦）
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory_items (
            id SERIAL PRIMARY KEY,
            code VARCHAR(30) NOT NULL UNIQUE,
            name VARCHAR(200),
            category VARCHAR(50),
            quantity INTEGER DEFAULT 0,
            online_quantity INTEGER DEFAULT 0,
            verified BOOLEAN DEFAULT FALSE,
            note TEXT,
            last_uploaded TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    conn.commit()
    print("✓ Tables initialized")

def load_dividend_data(conn):
    """載入 dividend_data.json"""
    with open(WORKSPACE / 'assets/dividend_data.json') as f:
        data = json.load(f)
    
    cur = conn.cursor()
    rows = data.get('tw', {}).get('confirmed', {}).get('rows', [])
    
    inserted = 0
    for r in rows:
        try:
            cur.execute("""
                INSERT INTO tw_dividend (code, period, cash_per_share, shares, amount_twd, ex_date, payout)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (code, period, ex_date) DO UPDATE SET
                    cash_per_share = EXCLUDED.cash_per_share,
                    shares = EXCLUDED.shares,
                    amount_twd = EXCLUDED.amount_twd,
                    payout = EXCLUDED.payout
            """, (
                r['code'], r['period'], r['cash'], r['shares'], r['amount'],
                r['ex_date'], r['payout']
            ))
            inserted += 1
        except Exception as e:
            print(f"  [WARN] {r['code']} {r['period']}: {e}")
    
    conn.commit()
    print(f"✓ tw_dividend: {inserted} rows")

def load_portfolio_data(conn):
    """載入 portfolio_data.json"""
    with open(WORKSPACE / 'assets/portfolio_data.json') as f:
        data = json.load(f)
    
    cur = conn.cursor()
    stocks = data.get('stocks', {})
    fx = data.get('fx', {}).get('USD_TWD', 31.5)
    
    # 台股
    for s in stocks.get('tw', []):
        mktval = s.get('market_value') or s.get('mktval', 0)
        cur.execute("""
            INSERT INTO portfolio_holdings 
            (market, symbol, name, shares, cost, price, market_value, gain, gain_pct,
             div, ann_div, div_yield, div_yield_cost, sector, update_time)
            VALUES ('TW', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (market, symbol) DO UPDATE SET
                name = EXCLUDED.name, shares = EXCLUDED.shares, cost = EXCLUDED.cost,
                price = EXCLUDED.price, market_value = EXCLUDED.market_value,
                gain = EXCLUDED.gain, gain_pct = EXCLUDED.gain_pct,
                div = EXCLUDED.div, ann_div = EXCLUDED.ann_div,
                div_yield = EXCLUDED.div_yield, div_yield_cost = EXCLUDED.div_yield_cost,
                sector = EXCLUDED.sector, update_time = EXCLUDED.update_time
        """, (
            s['symbol'], s['name'], s['shares'], s['cost'], s['price'],
            mktval, s.get('gain', 0), s.get('gain_pct', 0),
            s.get('div', 0), s.get('annDiv', 0), s.get('divYield', 0), s.get('divYieldCost', 0),
            s.get('sector', ''), s.get('update_time', None)
        ))
    
    # 美股（欄位名稱不同）
    for s in stocks.get('us', []):
        mktval_twd = s.get('mktvalTwd', 0)
        gain = s.get('gain', 0)
        ret_pct = s.get('retPct', 0)
        ann_div = s.get('annDivTwd', 0) or s.get('annDiv', 0)
        cur.execute("""
            INSERT INTO portfolio_holdings 
            (market, symbol, name, shares, cost, price, market_value, gain, gain_pct,
             div, ann_div, sector, update_time)
            VALUES ('US', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (market, symbol) DO UPDATE SET
                name = EXCLUDED.name, shares = EXCLUDED.shares, cost = EXCLUDED.cost,
                price = EXCLUDED.price, market_value = EXCLUDED.market_value,
                gain = EXCLUDED.gain, gain_pct = EXCLUDED.gain_pct,
                div = EXCLUDED.div, ann_div = EXCLUDED.ann_div, sector = EXCLUDED.sector,
                update_time = EXCLUDED.update_time
        """, (
            s['symbol'], s['name'], s['shares'], s['cost'], s['price'],
            mktval_twd, gain, ret_pct,
            s.get('div', 0), ann_div,
            s.get('sector', ''),
            s.get('update_time', None)
        ))
    
    conn.commit()
    tw_count = len(stocks.get('tw', []))
    us_count = len(stocks.get('us', []))
    print(f"✓ portfolio_holdings: {tw_count} TW + {us_count} US stocks")

def load_inventory_data(conn):
    """載入 inventory.json 和 senao_inventory.json"""
    cur = conn.cursor()
    
    total = 0
    for fname in ['inventory.json', 'senao_inventory.json']:
        path = WORKSPACE / fname
        if not path.exists():
            print(f"  [SKIP] {fname} not found")
            continue
        
        with open(path) as f:
            data = json.load(f)
        
        src = 'senio' if 'senao' in fname else 'senao'
        for cat in data.get('categories', []):
            cat_name = cat['name']
            for item in cat.get('items', []):
                cur.execute("""
                    INSERT INTO inventory_items 
                    (code, name, category, quantity, online_quantity, verified, note, last_uploaded)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (code) DO UPDATE SET
                        name = EXCLUDED.name, category = EXCLUDED.category,
                        quantity = EXCLUDED.quantity, online_quantity = EXCLUDED.online_quantity,
                        verified = EXCLUDED.verified, note = EXCLUDED.note,
                        last_uploaded = EXCLUDED.last_uploaded
                """, (
                    item['code'], item['name'], cat_name,
                    item.get('quantity', 0), item.get('onlineQuantity', 0),
                    item.get('verified', False), item.get('note', ''),
                    item.get('lastUploaded', None)
                ))
                total += 1
    
    conn.commit()
    print(f"✓ inventory_items: {total} items")

def main():
    print("=== SQL Migration: JSON → PostgreSQL ===\n")
    
    conn = get_conn()
    init_tables(conn)
    
    print("\n--- Loading Data ---")
    load_dividend_data(conn)
    load_portfolio_data(conn)
    load_inventory_data(conn)
    
    # Verify
    cur = conn.cursor()
    print("\n--- Verification ---")
    cur.execute("SELECT COUNT(*) FROM tw_dividend")
    print(f"  tw_dividend: {cur.fetchone()[0]} rows")
    cur.execute("SELECT COUNT(*) FROM portfolio_holdings")
    print(f"  portfolio_holdings: {cur.fetchone()[0]} rows")
    cur.execute("SELECT COUNT(*) FROM inventory_items")
    print(f"  inventory_items: {cur.fetchone()[0]} rows")
    
    conn.close()
    print("\n✓ Migration complete!")

if __name__ == '__main__':
    main()