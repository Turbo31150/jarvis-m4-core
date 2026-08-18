#!/usr/bin/env python3
"""
JARVIS System Daemon (Autonomie Totale Système)
Supervise et exécute en boucle fermée sans interruption :
1. Le tri et dépouillement réel de la Boîte de Réception IMAP (jarvis_mail_triage_live.py).
2. La chaîne d'orchestration Mega-Cycle (jarvis_intensive_runner.py).
Logue tous les événements dans jarvis_master.db.
"""
import sys
import os
import subprocess
import time
import sqlite3

DB_PATH = "/home/pamerys/jarvis/jarvis_master.db"
MAIL_SCRIPT = "/home/pamerys/jarvis/scripts/ops/jarvis_mail_triage_live.py"
MEGA_SCRIPT = "/home/pamerys/jarvis/scripts/ops/jarvis_intensive_runner.py"

def run_script(script_path):
    try:
        res = subprocess.run([sys.executable, script_path], capture_output=True, text=True, timeout=300)
        return res.returncode, res.stdout, res.stderr
    except Exception as e:
        return 1, "", str(e)

def log_system_event(event_name, code, latency_ms):
    try:
        # WAL : un seul écrivain à la fois sur une base très sollicitée,
        # il faut attendre au lieu d'échouer sur "database is locked".
        conn = sqlite3.connect(DB_PATH, timeout=120)
        conn.execute("PRAGMA busy_timeout=120000")
        conn.execute(
            "INSERT INTO pipeline_log (task_id, step, machine, model, latency_ms, quality_score) VALUES (?,?,?,?,?,?)",
            (7777, f"daemon_{event_name}", "M1", "system-daemon-v2", latency_ms, 1.0 if code == 0 else 0.0)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

def main():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ⚙️ Démarrage du DAEMON SYSTÈME AUTONOME JARVIS...")

    iteration = 1
    while True:
        print(f"\n--- 🔄 ITÉRATION DAEMON #{iteration} ---")

        # 1. Dépouillement Réel Boîte de Réception IMAP
        start_ts = time.time()
        code_mail, out_mail, err_mail = run_script(MAIL_SCRIPT)
        lat_mail = int((time.time() - start_ts) * 1000)
        log_system_event("mail_triage", code_mail, lat_mail)
        print(f"  [1/2] Mail Triage Live: Exit {code_mail} ({lat_mail}ms)")

        # 2. Mega-Cycle Intégral 7 Briques
        start_ts = time.time()
        code_mega, out_mega, err_mega = run_script(MEGA_SCRIPT)
        lat_mega = int((time.time() - start_ts) * 1000)
        log_system_event("mega_cycle", code_mega, lat_mega)
        print(f"  [2/2] Mega-Cycle 7 Briques: Exit {code_mega} ({lat_mega}ms)")

        iteration += 1
        time.sleep(10)

if __name__ == "__main__":
    main()
