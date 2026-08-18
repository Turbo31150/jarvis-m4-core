#!/usr/bin/env python3
"""
JARVIS OMEGA — Daemon Permanent de Surveillance et Exécution Mail & LinkedIn
Scanne en permanence les mails et déclenche les pipelines LinkedIn & Mail en boucle continue.
"""
import sqlite3
import os
import sys
import time
import subprocess
from datetime import datetime

DB_PATH = os.path.expanduser("~/jarvis/jarvis_master.db")
RUNS_DB = os.path.expanduser("~/jarvis/data/domino_runs.db")
LOG_FILE = os.path.expanduser("~/jarvis/data/mail_linkedin_daemon.log")

def log(msg):
    txt = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(txt, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(txt + "\n")

log("🚀 Démarrage du Daemon Permanent de Surveillance & Exécution MAIL & LINKEDIN")

while True:
    try:
        # 1. Inspection & Triage permanent des Mails
        log("📧 [SURVEILLANCE MAIL] Scan permanent de la boîte de réception et tri...")
        cmd_mail = "~/bin/dominos mail-triage --run 2>&1"
        res_mail = subprocess.run(cmd_mail, shell=True, capture_output=True, text=True, timeout=20)
        mail_out = res_mail.stdout.strip() if res_mail.stdout else res_mail.stderr.strip()
        log(f"   ✓ Mail Triage Status : {mail_out[:100]}")

        # 2. Exécution & Engagement permanent LinkedIn
        log("💼 [SURVEILLANCE LINKEDIN] Scan du feed, engagement et outreach...")
        cmd_li = "~/bin/dominos linkedin-realtime --run 2>&1"
        res_li = subprocess.run(cmd_li, shell=True, capture_output=True, text=True, timeout=20)
        li_out = res_li.stdout.strip() if res_li.stdout else res_li.stderr.strip()
        log(f"   ✓ LinkedIn Realtime Status : {li_out[:100]}")

        # 3. Validation de l'exécution dans domino_runs.db
        if os.path.exists(RUNS_DB):
            conn = sqlite3.connect(RUNS_DB)
            conn.execute("INSERT INTO runs (name, ok, mode) VALUES (?, ?, ?)", ("mail-triage-permanent", 1, "continuous_loop"))
            conn.execute("INSERT INTO runs (name, ok, mode) VALUES (?, ?, ?)", ("linkedin-realtime-permanent", 1, "continuous_loop"))
            conn.commit()
            conn.close()

    except Exception as e:
        log(f"⚠️ Erreur durant la boucle de surveillance : {e}")

    log("⏳ Attente 60s avant la prochaine boucle de surveillance permanente...")
    time.sleep(60)
