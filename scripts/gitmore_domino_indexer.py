#!/usr/bin/env python3
"""
gitmore_domino_indexer.py — Indexeur Scalable Instantané GITMORE & DOMINO (0-token).
Recherche ultra-rapide par signature, tag, ou mot-clé dans les 405+ cascades domino
et la bibliothèque vivante.
"""

import os
import json
import sqlite3
import glob

DB_PATH = os.path.expanduser("~/jarvis/jarvis_master.db")
DOMINOS_DIR = os.path.expanduser("~/jarvis/dominos-compiled/dominos")

def init_indexer_table():
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.execute("PRAGMA busy_timeout=120000")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gitmore_domino_index (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domino_name TEXT UNIQUE,
        signature TEXT,
        filepath TEXT,
        category TEXT,
        indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def build_index():
    init_indexer_table()
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.execute("PRAGMA busy_timeout=120000")
    cursor = conn.cursor()
    
    files = glob.glob(os.path.join(DOMINOS_DIR, "*.sh"))
    count = 0
    for f in files:
        bname = os.path.basename(f)
        sig = bname.replace(".sh", "").replace("-", "_")
        cursor.execute("""
        INSERT OR REPLACE INTO gitmore_domino_index (domino_name, signature, filepath, category)
        VALUES (?, ?, ?, ?)
        """, (bname, sig, f, "compiled_domino"))
        count += 1
        
    conn.commit()
    conn.close()
    return count

if __name__ == "__main__":
    total = build_index()
    print(f"🚀 Indexation Instantanée GITMORE DOMINO terminée : {total} cascades domino indexées par signature.")
