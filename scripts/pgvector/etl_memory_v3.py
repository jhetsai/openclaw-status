#!/usr/bin/env python3
"""
Ultra-lightweight ETL: Memory-Optimized
Strategy: Load model ONLY when needed, free immediately after use
"""

import os, re, gc, sys
from datetime import datetime

MEMORY_DIR = '/home/jhe/.openclaw/workspace/memory'
DB_CONFIG = {
    'host': '127.0.0.1', 'port': 5432,
    'dbname': 'openclaw', 'user': 'jhe',
    'password': 'openclaw_secure_pass_2026'
}

MAX_CHARS = 300
FILES_BEFORE_GC = 3   # GC every N files

def get_mem_mb():
    try:
        import tracemalloc
        c, _ = tracemalloc.get_traced_memory()
        return c / 1024 / 1024
    except:
        return 0

def chunk_text(text):
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'[#*`_~\[\]]', '', text)
    text = re.sub(r'\n+', '\n', text).strip()
    if len(text) <= MAX_CHARS:
        return [text] if text else []
    import jieba
    words = list(jieba.cut(text))
    chunks, cur, cur_len = [], [], 0
    for w in words:
        wl = len(w)
        if cur_len + wl > MAX_CHARS and cur:
            s = ''.join(cur)
            if s.strip(): chunks.append(s)
            cur = cur[-2:] + [w]
            cur_len = sum(len(x) for x in cur)
        else:
            cur.append(w)
            cur_len += wl
    if cur:
        s = ''.join(cur)
        if s.strip(): chunks.append(s)
    del words
    return chunks

def load_model():
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    return model

def process_with_model(model, chunks):
    from sentence_transformers import SentenceTransformer
    embeddings = model.encode(chunks)  # batch encode
    results = []
    for i, (c, e) in enumerate(zip(chunks, embeddings)):
        results.append((c, e.tolist()))
        del e
    del embeddings
    return results

print(f'[{datetime.now().strftime("%H:%M:%S")}] Starting ultra-light ETL')
print(f'[{datetime.now().strftime("%H:%M:%S")}] Memory: {get_mem_mb():.1f} MB')

import jieba
jieba.initialize()
print(f'[{datetime.now().strftime("%H:%M:%S")}] jieba ready')

# Collect file paths
file_paths = []
for root, dirs, filenames in os.walk(MEMORY_DIR):
    for fn in sorted(filenames):
        if fn.endswith('.md'):
            file_paths.append(os.path.join(root, fn))
print(f'[{datetime.now().strftime("%H:%M:%S")}] Found {len(file_paths)} files')

# Connect DB and clear
import psycopg2
conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()
cur.execute('TRUNCATE TABLE memory_chunks RESTART IDENTITY;')
conn.commit()
print(f'[{datetime.now().strftime("%H:%M:%S")}] DB cleared')

# Process files in ultra-small batches
model = None
total_chunks = 0
total_files = 0

for fpath in file_paths:
    rel = os.path.relpath(fpath, MEMORY_DIR)
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        continue
    
    if not content.strip():
        del content
        continue
    
    chunks = chunk_text(content)
    del content
    
    if not chunks:
        del chunks
        continue
    
    # Load model lazily (first file only, or if unloaded)
    if model is None:
        print(f'[{datetime.now().strftime("%H:%M:%S")}] Loading model...')
        model = load_model()
        print(f'[{datetime.now().strftime("%H:%M:%S")}] Model loaded. Memory: {get_mem_mb():.1f} MB')
    
    # Encode in sub-batches of 3 to minimize peak memory
    EMBED_BATCH = 3
    for b_start in range(0, len(chunks), EMBED_BATCH):
        b = chunks[b_start:b_start + EMBED_BATCH]
        embs = model.encode(b)
        for idx, (c, e) in enumerate(zip(b, embs)):
            cur.execute("""
                INSERT INTO memory_chunks (source_file, chunk_index, chunk_text, embedding)
                VALUES (%s, %s, %s, %s)
            """, (rel, b_start + idx, c, e.tolist()))
        del embs
        gc.collect()
    
    total_chunks += len(chunks)
    total_files += 1
    del chunks
    
    conn.commit()
    
    if total_files % FILES_BEFORE_GC == 0:
        gc.collect()
        print(f'[{datetime.now().strftime("%H:%M:%S")}] {total_files}/{len(file_paths)} files | {total_chunks} chunks | Mem: {get_mem_mb():.1f} MB')

# Final
if model is not None:
    del model
    gc.collect()

cur.execute('SELECT COUNT(*) FROM memory_chunks;')
cnt = cur.fetchone()[0]
print(f'[{datetime.now().strftime("%H:%M:%S")}] DONE! Total chunks: {cnt}')
conn.close()
gc.collect()
