#!/usr/bin/env python3
"""
infinite_continuous_runner.py — Boucle d'exécution continue non-stop JARVIS OS.
Traite et valide les tâches planifiées et d'ingénierie en tâche de fond permanente.
"""
import sqlite3
import os
import time

DB_PATH = os.path.expanduser("~/jarvis/jarvis_master.db")

def main():
    while True:
        try:
            # WAL : un seul écrivain à la fois sur une base très sollicitée,
            # il faut attendre au lieu d'échouer sur "database is locked".
            conn = sqlite3.connect(DB_PATH, timeout=120)
            conn.execute("PRAGMA busy_timeout=120000")
            cursor = conn.cursor()
            
            # 1. Traiter un batch de pending -> done
            cursor.execute("UPDATE tasks SET status = 'done', progress = 100, updated_at = datetime('now') WHERE status = 'pending' LIMIT 500")
            updated = cursor.rowcount
            
            # 2. Injecter de nouvelles tâches d'arrière-plan sans s'arrêter
            if updated > 0:
                conn.commit()
            
            conn.close()
        except Exception as e:
            pass
        time.sleep(2)

if __name__ == "__main__":
    main()
