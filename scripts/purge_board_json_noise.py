#!/usr/bin/env python3
"""
purge_board_json_noise.py — Purge des chunks de JSON brut inutile et optimisation du Board JARVIS.
"""

import os
import sys
import sqlite3
import time

DB_PATH = "/home/pamerys/jarvis/databases/board.db"

def purge_noise():
    print("==========================================================")
    print("🧹 [BOARD OS] PURGE DU BRUIT JSON ET OPTIMISATION VECTORIELLE")
    print("==========================================================")
    
    if not os.path.exists(DB_PATH):
        print(f"Erreur : {DB_PATH} introuvable.")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH, timeout=60.0)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    
    cur = conn.cursor()
    initial_count = cur.execute("SELECT count(*) FROM chunks").fetchone()[0]
    print(f"📊 Chunks initiaux en base : {initial_count}")
    
    # 1. Suppression des chunks de JSON brut inutile
    print("⏳ Suppression des chunks de JSON brut et logs techniques...")
    t0 = time.time()
    cur.execute("""
        DELETE FROM chunks 
        WHERE (text LIKE '{%' AND text LIKE '%}')
           OR (text LIKE '[%' AND text LIKE '%]')
           OR text LIKE '%"trace_id"%'
           OR text LIKE '%"schema_version"%'
    """)
    deleted = cur.rowcount
    conn.commit()
    t1 = time.time()
    
    remaining_count = cur.execute("SELECT count(*) FROM chunks").fetchone()[0]
    print(f"✅ {deleted} chunks de JSON brut purgés en {t1-t0:.2f}s !")
    print(f"📚 Chunks sains et doctrines conservés : {remaining_count}")
    
    # 2. Optimisation FTS et SQLite
    print("⏳ Optimisation de l'index FTS5 et vacuum...")
    try:
        cur.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('optimize');")
        conn.commit()
    except Exception as e:
        print(f"  (FTS optimize notice: {e})")
        
    conn.close()
    print("==========================================================")
    print("🎉 PURGE DU BOARD TERMINÉE AVEC SUCCÈS !")
    print("==========================================================")

if __name__ == "__main__":
    purge_noise()
