#!/usr/bin/env python3
"""
JARVIS-OMEGA — Permanent Continuous Vectorization Engine
========================================================
Indexation vectorielle locale continue (0-Token, 768 dims) :
  - Surveille les documents, notes, exports Notion, rapports et code
  - Découpe en chunks sémantiques
  - Génère les embeddings via LM Studio (127.0.0.1:1234)
  - Stocke les vecteurs denses dans jarvis_vector_store.db
"""

import os
import sys
import time
import json
import hashlib
import sqlite3
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

HOME = Path("/home/pamerys")
JARVIS_DIR = HOME / "jarvis"
DATA_DIR = JARVIS_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_VECTORS = DATA_DIR / "jarvis_vector_store.db"

WATCH_DIRS = [
    JARVIS_DIR / "reports",
    HOME / "labo" / "output",
    JARVIS_DIR / "board",
    JARVIS_DIR / "data"
]

EMBED_URL = "http://127.0.0.1:1234/v1/embeddings"
EMBED_MODEL = "text-embedding-nomic-embed-text-v1.5"

def ts_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def log(msg):
    print(f"[{ts_now()}] 🧬 [VECTOR-ENGINE] {msg}", flush=True)

def init_db():
    with sqlite3.connect(str(DB_VECTORS)) as cx:
        cx.execute("PRAGMA journal_mode = WAL;")
        cx.execute("PRAGMA busy_timeout = 60000;")
        cx.execute("""
            CREATE TABLE IF NOT EXISTS indexed_files (
                filepath TEXT PRIMARY KEY,
                file_hash TEXT,
                chunks_count INTEGER,
                last_indexed DATETIME
            )
        """)
        cx.execute("""
            CREATE TABLE IF NOT EXISTS document_vectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT,
                chunk_index INTEGER,
                chunk_text TEXT,
                embedding_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cx.execute("CREATE INDEX IF NOT EXISTS idx_doc_path ON document_vectors(filepath);")

def get_embedding(text: str) -> list:
    payload = {"model": EMBED_MODEL, "input": text[:2000]}
    req = urllib.request.Request(
        EMBED_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        return data.get('data', [{}])[0].get('embedding', [])

def chunk_text(text: str, chunk_size=800, overlap=100) -> list:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def process_file(filepath: Path):
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
        if not content.strip():
            return
        
        file_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        with sqlite3.connect(str(DB_VECTORS), timeout=20) as cx:
            row = cx.execute("SELECT file_hash FROM indexed_files WHERE filepath=?", (str(filepath),)).fetchone()
            if row and row[0] == file_hash:
                return # Déjà à jour
        
        chunks = chunk_text(content)
        vectors = []
        for idx, ch in enumerate(chunks):
            emb = get_embedding(ch)
            if emb:
                vectors.append((str(filepath), idx, ch, json.dumps(emb)))
        
        with sqlite3.connect(str(DB_VECTORS), timeout=20) as cx:
            cx.execute("DELETE FROM document_vectors WHERE filepath=?", (str(filepath),))
            cx.executemany("""
                INSERT INTO document_vectors (filepath, chunk_index, chunk_text, embedding_json)
                VALUES (?, ?, ?, ?)
            """, vectors)
            cx.execute("""
                INSERT OR REPLACE INTO indexed_files (filepath, file_hash, chunks_count, last_indexed)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (str(filepath), file_hash, len(vectors)))
            
        log(f"✓ Vectorisé : {filepath.name} ({len(vectors)} chunks 768d)")
    except Exception as e:
        log(f"Erreur sur {filepath.name}: {e}")

def run_vectorizer_loop():
    log("🚀 Démarrage du Démon Permanent de Vectorisation Locale...")
    init_db()
    
    while True:
        try:
            total_indexed = 0
            for d in WATCH_DIRS:
                if not d.exists(): continue
                for ext in ["*.md", "*.txt", "*.json", "*.py"]:
                    for f in d.rglob(ext):
                        if f.is_file() and f.stat().st_size < 500000:
                            process_file(f)
            
            with sqlite3.connect(str(DB_VECTORS)) as cx:
                total_vecs = cx.execute("SELECT count(*) FROM document_vectors").fetchone()[0]
                total_files = cx.execute("SELECT count(*) FROM indexed_files").fetchone()[0]
            
            # log(f"📊 Base vectorielle : {total_files} fichiers · {total_vecs} vecteurs denses indexés.")
            time.sleep(30)
        except Exception as e:
            log(f"Erreur boucle vectorisation: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_vectorizer_loop()
