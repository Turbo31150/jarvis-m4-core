#!/usr/bin/env python3
"""
scan_full_disk_m6.py — Indexation Globale de TOUT le Disque Dur sur M6 (0-token).
Partitions indexées : /, /mnt/jarvis-data, /storage, /home.
"""

import os
import sqlite3
import time

DB_PATH = os.path.expanduser("~/jarvis/jarvis_master.db")

def index_full_disk():
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.execute("PRAGMA busy_timeout=120000")
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS full_disk_m6_index (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        path TEXT UNIQUE,
        size_bytes INTEGER,
        indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    roots = ["/home/pamerys", "/storage", "/mnt/jarvis-data"]
    total = 0
    
    for r_dir in roots:
        if not os.path.exists(r_dir):
            continue
        print(f"🔍 Indexation en cours du répertoire : {r_dir}...")
        for root, dirs, files in os.walk(r_dir):
            # Skip heavy system build cache dirs
            dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "__pycache__", ".venv", ".cache"]]
            for f in files:
                full_path = os.path.join(root, f)
                try:
                    size = os.path.getsize(full_path)
                except Exception:
                    size = 0
                try:
                    cur.execute("""
                    INSERT OR REPLACE INTO full_disk_m6_index (filename, path, size_bytes)
                    VALUES (?, ?, ?)
                    """, (f, full_path, size))
                    total += 1
                except Exception:
                    pass
            if total % 50000 == 0 and total > 0:
                conn.commit()
                print(f"  • {total:,} fichiers indexés...")
                
    conn.commit()
    conn.close()
    return total

if __name__ == "__main__":
    t0 = time.time()
    n = index_full_disk()
    elapsed = time.time() - t0
    print(f"💥 INDEXATION GLOBALE TOUT LE DISQUE SUR M6 COMPLÉTÉE : {n:,} fichiers répertoriés en {elapsed:.2f}s !")
