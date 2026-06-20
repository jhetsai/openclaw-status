#!/usr/bin/env python3
"""
ETL: Electricity → pgvector chunks
Reads electricity_meters + electricity_bills → generates descriptive text → embeds → stores in PostgreSQL
"""
import subprocess, os, json, sys

# === Config ===
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
TABLE = "electricity_chunks"
DIM = 384

def sql(query):
    result = subprocess.run(
        ['docker', 'exec', 'pgvector_db', 'psql', '-U', 'jhe', '-d', 'openclaw', '-t', '-c', query],
        capture_output=True, text=True
    )
    return result.stdout.strip(), result.returncode

def query_electricity():
    """Fetch all electricity data from PostgreSQL"""
    meters = {}
    meter_rows, _ = sql("SELECT account_id, meter_type, address, feeder FROM electricity_meters ORDER BY account_id;")
    for row in meter_rows.split('\n'):
        if not row.strip():
            continue
        parts = [p.strip() for p in row.split('|')]
        if len(parts) >= 4:
            meters[parts[0]] = {'type': parts[1], 'address': parts[2], 'feeder': parts[3]}

    bills = {}
    bill_rows, _ = sql("SELECT account_id, period, yyyy, kwh, cost FROM electricity_bills ORDER BY account_id, period;")
    for row in bill_rows.split('\n'):
        if not row.strip():
            continue
        parts = [p.strip() for p in row.split('|')]
        if len(parts) >= 5:
            acct = parts[0]
            if acct not in bills:
                bills[acct] = []
            bills[acct].append({
                'period': parts[1],
                'yyyy': int(parts[2]),
                'kwh': int(parts[3]),
                'cost': int(parts[4])
            })

    return meters, bills

def generate_chunk_text(meter_id, meter_info, bills):
    """Generate descriptive text for a single meter"""
    periods_label = {
        '11311': '113年11月', '11401': '114年1月', '11403': '114年3月',
        '11405': '114年5月', '11407': '114年7月', '11409': '114年9月',
        '11411': '114年11月', '11501': '115年1月', '11503': '115年3月'
    }

    b = bills.get(meter_id, [])
    if not b:
        return None

    mi = meter_info
    total_kwh = sum(x['kwh'] for x in b)
    total_cost = sum(x['cost'] for x in b)
    avg_kwh = total_kwh / len(b) if b else 0
    avg_cost_per_kwh = total_cost / total_kwh if total_kwh else 0
    max_bill = max(b, key=lambda x: x['kwh']) if b else None
    min_bill = min(b, key=lambda x: x['kwh']) if b else None

    # Latest period
    latest = b[-1] if b else None

    # High consumption periods
    high_periods = [x for x in b if x['kwh'] > avg_kwh * 1.3] if avg_kwh else []

    lines = [
        f"電號：{meter_id}",
        f"用途：{mi['type']}",
        f"地址：{mi['address']}",
        f"饋線：{mi['feeder']}",
        f"總用電：{total_kwh:,} 度（{len(b)} 期）",
        f"平均每期用電：{avg_kwh:.0f} 度",
        f"平均電費：{total_cost:,} 元",
        f"平均電價：{avg_cost_per_kwh:.2f} 元/度",
    ]

    if max_bill:
        p = periods_label.get(max_bill['period'], max_bill['period'])
        lines.append(f"最高用電：{max_bill['kwh']} 度（{p}）")

    if min_bill:
        p = periods_label.get(min_bill['period'], min_bill['period'])
        lines.append(f"最低用電：{min_bill['kwh']} 度（{p}）")

    if latest:
        p = periods_label.get(latest['period'], latest['period'])
        lines.append(f"最近一期（{p}）：{latest['kwh']} 度，{latest['cost']} 元")

    if high_periods:
        periods_str = '、'.join(periods_label.get(x['period'], x['period']) for x in high_periods[:3])
        lines.append(f"用電高峰：{periods_str}")

    return '。'.join(lines) + '。'

def setup_table():
    """Create the electricity_chunks table"""
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {TABLE} (
        id SERIAL PRIMARY KEY,
        account_id VARCHAR(50) NOT NULL,
        chunk_text TEXT NOT NULL,
        embedding vector({DIM}),
        created_at TIMESTAMP DEFAULT NOW()
    );
    DROP INDEX IF EXISTS {TABLE}_embedding_idx;
    CREATE INDEX {TABLE}_embedding_idx ON {TABLE} USING ivfflat (embedding vector_cosine_ops);
    """
    # Split and run each statement
    for stmt in create_sql.split(';'):
        stmt = stmt.strip()
        if stmt:
            sql(stmt + ";")
    print("  Table created/verified")

def embed_texts(texts):
    """Embed texts using sentence-transformers"""
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBED_MODEL)
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()

def etl():
    print("[ETL] Starting electricity → pgvector")
    
    # 1. Fetch data
    print("[ETL] Fetching electricity data from PostgreSQL...")
    meters, bills = query_electricity()
    print(f"  Meters: {len(meters)}, Bills: {sum(len(v) for v in bills.values())} rows")
    
    # 2. Setup table
    print("[ETL] Setting up table...")
    setup_table()
    
    # 3. Clear old chunks
    sql(f"DELETE FROM {TABLE};")
    
    # 4. Generate texts
    print("[ETL] Generating chunk texts...")
    chunks = []
    for meter_id, meter_info in meters.items():
        text = generate_chunk_text(meter_id, meter_info, bills)
        if text:
            chunks.append((meter_id, text))
    
    print(f"  Generated {len(chunks)} chunks")
    
    # 5. Embed
    print("[ETL] Embedding chunks...")
    texts = [c[1] for c in chunks]
    embeddings = embed_texts(texts)
    
    # 6. Insert
    print("[ETL] Inserting into PostgreSQL...")
    for (meter_id, text), embedding in zip(chunks, embeddings):
        emb_str = '[' + ','.join(f'{v:.6f}' for v in embedding) + ']'
        insert_sql = f"INSERT INTO {TABLE} (account_id, chunk_text, embedding) VALUES ('{meter_id}', $CHUNK${text}$CHUNK$, '{emb_str}'::vector);"
        sql(insert_sql)
    
    # Verify
    result, _ = sql(f"SELECT COUNT(*) FROM {TABLE};")
    print(f"[ETL] Done. Total chunks: {result}")

if __name__ == '__main__':
    etl()