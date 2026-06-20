#!/usr/bin/env python3
"""
ETL script: Memory to Vector Database - Memory Optimized Version
Processes files ONE AT A TIME to minimize memory footprint
"""

import os
import re
import gc
import psycopg2
from sentence_transformers import SentenceTransformer
import jieba
from datetime import datetime
import tracemalloc

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
MAX_CHUNK_CHARS = 300
BATCH_SIZE = 5  # Smaller batch for lower memory

def get_mem_mb():
    try:
        current, _ = tracemalloc.get_traced_memory()
        return current / 1024 / 1024
    except:
        return 0.0

def chunk_text(text, max_chars=MAX_CHUNK_CHARS):
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
    
    del words
    return chunks

def main():
    tracemalloc.start()
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Starting ETL (memory optimized)...')
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Memory at start: {get_mem_mb():.1f} MB')
    
    # Initialize jieba
    jieba.initialize()
    print(f'[{datetime.now().strftime("%H:%M:%S")}] jieba dict loaded')
    
    # Load model ONCE
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Loading embedding model...')
    model = SentenceTransformer(MODEL_NAME)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Model loaded: {model.device}')
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Memory after model: {get_mem_mb():.1f} MB')
    
    # Collect file paths ONLY (not content) - memory efficient
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Scanning memory files...')
    file_paths = []
    for root, dirs, filenames in os.walk(MEMORY_DIR):
        for fname in sorted(filenames):
            if fname.endswith('.md'):
                fpath = os.path.join(root, fname)
                file_paths.append(fpath)
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Found {len(file_paths)} files')
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Memory: {get_mem_mb():.1f} MB')
    
    # Connect to DB
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Clear existing data
    cur.execute('TRUNCATE TABLE memory_chunks RESTART IDENTITY;')
    conn.commit()
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Cleared old data')
    
    total_chunks = 0
    total_files = 0
    
    for fpath in file_paths:
        rel_path = os.path.relpath(fpath, MEMORY_DIR)
        
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f'Error reading {fpath}: {e}')
            continue
        
        if not content.strip():
            del content
            continue
        
        # Split into chunks
        chunks = chunk_text(content)
        del content  # IMMEDIATELY free content after chunking
        
        if not chunks:
            del chunks
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
            
            # Clear embeddings immediately after insert
            del embeddings
        
        total_chunks += len(chunks)
        total_files += 1
        del chunks
        
        # Commit after each file
        conn.commit()
        
        # Aggressive memory cleanup every 10 files
        if total_files % 10 == 0:
            gc.collect(1)
            print(f'[{datetime.now().strftime("%H:%M:%S")}] Files: {total_files}/{len(file_paths)} | Chunks: {total_chunks} | Mem: {get_mem_mb():.1f} MB')
    
    # Final stats
    cur.execute('SELECT COUNT(*) FROM memory_chunks;')
    count = cur.fetchone()[0]
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] ETL complete!')
    print(f'  Files processed: {total_files}')
    print(f'  Total chunks: {count}')
    print(f'  Peak memory: {peak/1024/1024:.1f} MB')
    print(f'  Final memory: {get_mem_mb():.1f} MB')
    
    conn.close()
    
    # Force final GC
    gc.collect()

if __name__ == '__main__':
    main()
