#!/usr/bin/env python3
"""
ETL script: Memory to Vector Database - Low Memory Version
Processes files one at a time with explicit memory management
"""

import os
import re
import gc
import psycopg2
from sentence_transformers import SentenceTransformer
import jieba
from datetime import datetime

# Config
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'dbname': 'openclaw',
    'user': 'jhe',
    'password': 'openclaw_secure_pass_2026'
}

MEMORY_DIR = '/home/jhe/.openclaw/workspace/memory'
MODEL_NAME = 'all-MiniLM-L6-v2'
MAX_CHUNK_CHARS = 300  # Conservative chunk size
BATCH_SIZE = 10  # Process 10 chunks at a time

def init_jieba():
    """Initialize jieba dict once"""
    import jieba
    jieba.initialize()
    print(f'[{datetime.now().strftime("%H:%M:%S")}] jieba dict loaded')

def chunk_text(text, max_chars=MAX_CHUNK_CHARS):
    """Split text into chunks using jieba word segmentation"""
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'[#*`_~\[\]]', '', text)
    text = re.sub(r'\n+', '\n', text).strip()
    
    if len(text) <= max_chars:
        return [text] if text else []
    
    words = list(jieba.cut(text))
    chunks = []
    current_chunk = []
    current_len = 0
    
    for word in words:
        word_len = len(word)
        if current_len + word_len > max_chars and current_chunk:
            chunk_str = ''.join(current_chunk)
            if chunk_str.strip():
                chunks.append(chunk_str)
            overlap_words = current_chunk[-3:] if len(current_chunk) >= 3 else current_chunk
            current_chunk = overlap_words + [word]
            current_len = sum(len(w) for w in current_chunk)
        else:
            current_chunk.append(word)
            current_len += word_len
    
    if current_chunk:
        chunk_str = ''.join(current_chunk)
        if chunk_str.strip():
            chunks.append(chunk_str)
    
    return chunks

def main():
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Starting ETL (low memory version)...')
    
    # Initialize jieba first (before model loads)
    init_jieba()
    
    # Load model
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Loading embedding model...')
    model = SentenceTransformer(MODEL_NAME)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Model loaded: {model.device}')
    
    # Collect all files
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Scanning memory files...')
    files_data = []
    for root, dirs, filenames in os.walk(MEMORY_DIR):
        for fname in sorted(filenames):
            if fname.endswith('.md'):
                fpath = os.path.join(root, fname)
                rel_path = os.path.relpath(fpath, MEMORY_DIR)
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if content.strip():
                        files_data.append({'file': rel_path, 'content': content})
                except Exception as e:
                    print(f'Error reading {fpath}: {e}')
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Found {len(files_data)} files with content')
    
    # Connect to DB
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Clear existing data
    cur.execute('TRUNCATE TABLE memory_chunks RESTART IDENTITY;')
    conn.commit()
    
    total_chunks = 0
    total_files = 0
    
    for file_data in files_data:
        rel_path = file_data['file']
        content = file_data['content']
        
        # Split into chunks
        chunks = chunk_text(content)
        
        if not chunks:
            continue
        
        # Process chunks in small batches
        for batch_start in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[batch_start:batch_start + BATCH_SIZE]
            embeddings = model.encode(batch)
            
            for idx, (chunk_str, embedding) in enumerate(zip(batch, embeddings)):
                cur.execute("""
                    INSERT INTO memory_chunks (source_file, chunk_index, chunk_text, embedding)
                    VALUES (%s, %s, %s, %s)
                """, (rel_path, batch_start + idx, chunk_str, embedding.tolist()))
        
        total_chunks += len(chunks)
        total_files += 1
        
        # Commit after each file and force GC
        conn.commit()
        del chunks, embeddings
        gc.collect()
        
        if total_files % 20 == 0:
            print(f'[{datetime.now().strftime("%H:%M:%S")}] Processed {total_files}/{len(files_data)} files ({total_chunks} chunks)')
    
    # Final stats
    cur.execute('SELECT COUNT(*) FROM memory_chunks;')
    count = cur.fetchone()[0]
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] ETL complete!')
    print(f'  Files processed: {total_files}')
    print(f'  Total chunks: {count}')
    
    conn.close()

if __name__ == '__main__':
    main()