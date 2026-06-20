#!/usr/bin/env python3
"""
ETL: Work Schedule → pgvector chunks
Reads work_schedule from PostgreSQL → generates descriptive text → embeds → stores in PostgreSQL
"""
import subprocess, os
from sentence_transformers import SentenceTransformer

EMBED_MODEL = "all-MiniLM-L6-v2"
TABLE = "work_schedule_chunks"
DIM = 384

def sql(q):
    r = subprocess.run(['docker', 'exec', 'pgvector_db', 'psql', '-U', 'jhe', '-d', 'openclaw', '-t', '-c', q], capture_output=True, text=True)
    return r.stdout.strip()

def setup_table():
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {TABLE} (
        id SERIAL PRIMARY KEY,
        work_date DATE NOT NULL,
        chunk_text TEXT NOT NULL,
        embedding vector({DIM}),
        created_at TIMESTAMP DEFAULT NOW()
    );
    DROP INDEX IF EXISTS {TABLE}_embedding_idx;
    CREATE INDEX {TABLE}_embedding_idx ON {TABLE} USING ivfflat (embedding vector_cosine_ops);
    """
    for stmt in create_sql.split(';'):
        if stmt.strip():
            sql(stmt + ";")
    print("  Table created/verified")

def get_schedule():
    rows = sql("SELECT work_date, start_time, end_time, work_hours, is_holiday, notes FROM work_schedule ORDER BY work_date;").split('\n')
    schedule = []
    for row in rows:
        if not row.strip():
            continue
        parts = [p.strip() for p in row.split('|')]
        if len(parts) >= 6:
            schedule.append({
                'date': parts[0],
                'start': parts[1] or None,
                'end': parts[2] or None,
                'hours': float(parts[3]) if parts[3] else 0,
                'holiday': parts[4] == 't',
                'notes': parts[5] or ''
            })
    return schedule

def generate_text(entry):
    date_str = entry['date']  # YYYY-MM-DD
    y, m, d = date_str.split('-')
    month_day = f"{int(m)}月{int(d)}日"
    
    if entry['holiday']:
        return f"{month_day}：休假日。"
    
    start = entry['start'] or '?'
    end = entry['end'] or '?'
    hours = entry['hours']
    notes = f"（{entry['notes']}）" if entry['notes'] else ''
    
    return f"{month_day}：上班{start}~{end}，共{hours}小時。{notes}"

def etl():
    print("[ETL] Starting work_schedule → pgvector")
    
    schedule = get_schedule()
    print(f"  Fetched {len(schedule)} schedule entries")
    
    setup_table()
    sql(f"DELETE FROM {TABLE};")
    
    texts = [generate_text(e) for e in schedule]
    
    print(f"  Embedding {len(texts)} chunks...")
    model = SentenceTransformer(EMBED_MODEL)
    embeddings = model.encode(texts, show_progress_bar=False)
    
    for entry, text, emb in zip(schedule, texts, embeddings.tolist()):
        emb_str = '[' + ','.join(f'{v:.6f}' for v in emb) + ']'
        sql(f"INSERT INTO {TABLE} (work_date, chunk_text, embedding) VALUES ('{entry['date']}', $CHUNK${text}$CHUNK$, '{emb_str}'::vector);")
    
    result = sql(f"SELECT COUNT(*) FROM {TABLE};")
    print(f"[ETL] Done. Total chunks: {result}")

if __name__ == '__main__':
    etl()