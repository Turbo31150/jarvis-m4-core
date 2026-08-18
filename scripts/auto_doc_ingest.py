#!/usr/bin/env python3
"""
JARVIS AUTO DOC INGESTION & SCRAPING ENGINE
1. Scrape et avale la documentation web/sources.
2. Indexe les données dans la base SQLite locale.
3. Transmet le contenu prétraité au tampon M6.
"""
import os, sys, json, sqlite3, time, urllib.request

ROOT = "/home/pamerys/jarvis"
DB_PATH = f"{ROOT}/jarvis_master.db"

def ingest_url_sources(url_list):
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.execute("PRAGMA busy_timeout=120000")
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS web_ingested_docs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        content TEXT,
        status TEXT,
        ts TEXT
    );
    """)
    
    ingested_count = 0
    for url in url_list:
        try:
            print(f"🌐 Ingestion source : {url}...")
            req = urllib.request.Request(url, headers={'User-Agent': 'JARVIS-Doc-Ingest/1.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                ts = time.strftime('%Y-%m-%d %H:%M:%S')
                cur.execute("""
                INSERT INTO web_ingested_docs (url, content, status, ts)
                VALUES (?, ?, 'INGESTED', ?)
                ON CONFLICT(url) DO UPDATE SET content=excluded.content, ts=excluded.ts;
                """, (url, html[:10000], ts))
                ingested_count += 1
                print(f"✅ Source avalée ({len(html)} octets) -> SQLite.")
        except Exception as e:
            print(f"⚠️ Erreur ingestion {url}: {e}")
            
    conn.commit()
    conn.close()
    print(f"🏁 Total sources avalées et indexées : {ingested_count}")

if __name__ == "__main__":
    sources = [
        "https://raw.githubusercontent.com/ollama/ollama/main/README.md",
        "https://raw.githubusercontent.com/vllm-project/vllm/main/README.md"
    ]
    ingest_url_sources(sources)
