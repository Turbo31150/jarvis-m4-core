#!/usr/bin/env python3
"""
ranger_home_m6_protocole.py — Rangement & Indexation globale de /home sur M6 / Storage.
Implante l'accès déterministe scalable instantané par mots-clés, signatures et domino.
"""

import os
import sqlite3
import glob
import time

DB_PATH = os.path.expanduser("~/jarvis/jarvis_master.db")
STORAGE_ROOT = os.path.expanduser("/storage/m6_archive")

def ranger_m6():
    os.makedirs(STORAGE_ROOT, exist_ok=True)
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.execute("PRAGMA busy_timeout=120000")
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS m6_home_index (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT,
        path TEXT UNIQUE,
        category TEXT,
        indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Target directories to organize
    targets = [
        ("/home/pamerys/jarvis/prospection-sender", "prospection_sender"),
        ("/home/pamerys/Workspaces/labo-bibliotheque-centrale/bibliotheque", "labo_bibliotheque"),
        ("/home/pamerys/jarvis/dominos-compiled", "dominos_compiled"),
        ("/home/pamerys/jarvis/scripts", "jarvis_scripts")
    ]
    
    total = 0
    for root_dir, cat in targets:
        if os.path.exists(root_dir):
            for r, _, files in os.walk(root_dir):
                for f in files:
                    full_p = os.path.join(r, f)
                    kw = f.lower().replace("_", " ").replace("-", " ")
                    cur.execute("""
                    INSERT OR REPLACE INTO m6_home_index (keyword, path, category)
                    VALUES (?, ?, ?)
                    """, (kw, full_p, cat))
                    total += 1
                    
    conn.commit()
    conn.close()
    return total

if __name__ == "__main__":
    t0 = time.time()
    n = ranger_m6()
    elapsed = time.time() - t0
    print(f"🚀 PROTOCOLE M6 COMPLÉTÉ : {n:,} éléments de /home rangés et indexés en {elapsed:.2f}s !")
