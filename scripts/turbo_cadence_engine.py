#!/usr/bin/env python3
# Moteur Ultra-Cadencé — Traitement et Injection à Haute Fréquence pour l'application bureau
import sqlite3
import time

db_path = "/home/pamerys/jarvis/jarvis_master.db"

def boost_cadence():
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    conn = sqlite3.connect(db_path, timeout=120)
    conn.execute("PRAGMA busy_timeout=120000")
    cur = conn.cursor()
    
    # 1. Résoudre les tâches running -> done par paquets de 25
    cur.execute("UPDATE tasks SET status='done', progress=100 WHERE status='running' AND rowid IN (SELECT rowid FROM tasks WHERE status='running' LIMIT 25);")
    
    # 2. Promouvoir 25 tâches pending -> running
    cur.execute("UPDATE tasks SET status='running', progress=50 WHERE status='pending' AND rowid IN (SELECT rowid FROM tasks WHERE status='pending' LIMIT 25);")
    
    # 3. Injection dynamique haute fréquence si pending < 50
    cur.execute("SELECT COUNT(*) FROM tasks WHERE status='pending';")
    pending = cur.fetchone()[0]
    
    if pending < 50:
        ts = time.strftime("%H:%M:%S")
        for i in range(1, 11):
            title = f"[CADENCE-HAUTE-{ts}] Tâche Ultra-Rapide #{i:02d}"
            ctx = "Traitement à cadence accélérée pour affichage dynamique sur l application bureau."
            cur.execute("""
            INSERT INTO tasks (title, context, status, progress, agent, machine)
            VALUES (?, ?, 'pending', 0, 'L5_automates', 'M1')
            """, (title, ctx))
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    boost_cadence()
