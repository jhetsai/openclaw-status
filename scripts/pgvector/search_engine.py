#!/usr/bin/env python3
"""
Interactive Vector Search Engine
Supports searching both memory_chunks and stock_chunks
Usage: python3 search_engine.py [memory|stock|all]
Then type queries, one per line. Type 'quit' or 'exit' to exit.
Output is JSON for easy parsing.
"""

import sys
import json
import psycopg2
from sentence_transformers import SentenceTransformer

# Config
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'dbname': 'openclaw',
    'user': 'jhe',
    'password': 'openclaw_secure_pass_2026'
}

MODEL_NAME = 'all-MiniLM-L6-v2'
TOP_K = 5  # Return top K results per table

def search_memory(query, model, cur, top_k=TOP_K):
    """Search memory_chunks table"""
    try:
        query_embedding = model.encode([query])[0]
        
        cur.execute("""
            SELECT 'memory' AS source, source_file AS file, chunk_index, chunk_text,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM memory_chunks
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """, (query_embedding.tolist(), query_embedding.tolist(), top_k))
        
        results = cur.fetchall()
        return [{
            'source': 'memory',
            'file': r[1],
            'chunk': r[2],
            'text': r[3],
            'score': round(r[4], 4)
        } for r in results]
    except Exception as e:
        return {'error': str(e)}

def search_stock(query, model, cur, top_k=TOP_K):
    """Search stock_chunks table"""
    try:
        query_embedding = model.encode([query])[0]
        
        cur.execute("""
            SELECT 'stock' AS source, stock_code AS file, 0 AS chunk_index, chunk_text,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM stock_chunks
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """, (query_embedding.tolist(), query_embedding.tolist(), top_k))
        
        results = cur.fetchall()
        return [{
            'source': 'stock',
            'file': r[1],
            'chunk': r[2],
            'text': r[3],
            'score': round(r[4], 4)
        } for r in results]
    except Exception as e:
        return {'error': str(e)}

def main():
    # Determine search mode
    mode = 'all'  # default
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    
    print(f'# Vector Search Engine ready (mode: {mode})', file=sys.stderr)
    print(f'# Type queries, one per line. Type "quit" or "exit" to exit.', file=sys.stderr)
    print(f'# Output is JSON.', file=sys.stderr)
    sys.stderr.flush()
    
    # Load model once
    model = SentenceTransformer(MODEL_NAME)
    
    # Connect to DB
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Process input line by line
    for line in sys.stdin:
        query = line.strip()
        
        if query.lower() in ('quit', 'exit', 'q'):
            print('# Exiting...', file=sys.stderr)
            break
        
        if not query:
            print(json.dumps({'error': 'empty query'}))
            sys.stdout.flush()
            continue
        
        results = []
        
        if mode in ('all', 'memory'):
            results.extend(search_memory(query, model, cur))
        
        if mode in ('all', 'stock'):
            results.extend(search_stock(query, model, cur))
        
        # Sort by score descending
        if results and isinstance(results, list) and 'error' not in results[0]:
            results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        print(json.dumps(results, ensure_ascii=False))
        sys.stdout.flush()
    
    conn.close()

if __name__ == '__main__':
    main()