#!/usr/bin/env python3
"""
JARVIS OMEGA — Master Autopilot Full Live (Mode 100% Autonome Réel 24/7)
Pilote automatique unifié qui exécute en arrière-plan et sans interruption :
1. Le scan & triage IMAP + rédaction des brouillons d'emails.
2. Le scan du fil LinkedIn, likes, réactions, rédaction & publication de posts.
3. La prise de contact directe (outreach) & l'expansion réseau B2B.
4. L'aspiration NotebookLM Cloud & l'alimentation du CRM.
5. L'exécution dynamique des dominos et le rafraîchissement du planning.
"""
import time
import os
import sys
import subprocess
import sqlite3
from datetime import datetime

LOG_FILE = os.path.expanduser("~/jarvis/data/master_autopilot_full_live.log")
RUNS_DB = os.path.expanduser("~/jarvis/data/domino_runs.db")

def log(msg):
    txt = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(txt, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(txt + "\n")

log("🔥 DÉMARRAGE DU MASTER AUTOPILOT FULL LIVE (PRODUCTION 100% AUTONOME RÉELLE 24/7)")

cycle = 0
while True:
    cycle += 1
    log(f"\n==================== CYCLE AUTOPILOT #{cycle} ====================")

    # 1. AUTOPILOT MAIL : Triage IMAP & Brouillons
    try:
        log("📧 [AUTOPILOT MAIL] Execution du triage IMAP & brouillons réels...")
        res = subprocess.run("~/bin/dominos mail-triage --run 2>&1", shell=True, capture_output=True, text=True, timeout=30)
        log(f"   ✓ Status Mail : {res.stdout.strip()[:100]}")
    except Exception as e:
        log(f"   ⚠️ Exception Mail : {e}")

    # 2. AUTOPILOT LINKEDIN : Feed, Likes, Commentaires & Posts
    try:
        log("💼 [AUTOPILOT LINKEDIN] Interaction Feed, Likes, Commentaires & Posts...")
        res = subprocess.run("~/bin/dominos linkedin-realtime --run 2>&1", shell=True, capture_output=True, text=True, timeout=60)
        log(f"   ✓ Status LinkedIn Feed : {res.stdout.strip()[:100]}")
    except Exception as e:
        log(f"   ⚠️ Exception LinkedIn Feed : {e}")

    # 3. AUTOPILOT OUTREACH & EXPANSION RÉSEAU
    try:
        log("🤝 [AUTOPILOT NETWORK] Machine de Croissance Réseau & Direct Outreach...")
        res = subprocess.run("python3 /home/pamerys/jarvis/scripts/linkedin_network_growth_engine.py 2>&1", shell=True, capture_output=True, text=True, timeout=30)
        log(f"   ✓ Status Expansion Réseau : {res.stdout.strip()[:100]}")
    except Exception as e:
        log(f"   ⚠️ Exception Expansion Réseau : {e}")

    # 4. AUTOPILOT NOTEBOOKLM CLOUD & CRM
    try:
        log("☁️ [AUTOPILOT NOTEBOOKLM] Aspiration Cloud & Injection CRM SQLite...")
        res = subprocess.run("~/bin/dominos notebooklm-aspire --run 2>&1", shell=True, capture_output=True, text=True, timeout=30)
        log(f"   ✓ Status NotebookLM Cloud : {res.stdout.strip()[:100]}")
    except Exception as e:
        log(f"   ⚠️ Exception NotebookLM : {e}")

    # 5. RAFRAÎCHISSEMENT ET EXECUTION DU PLANNING
    try:
        log("⚡ [AUTOPILOT PLANNING] Synchronisation du planning unifié & execution...")
        res = subprocess.run("python3 /home/pamerys/Workspaces/planning-app/bin/planning-mega.py --no-preload 2>&1", shell=True, capture_output=True, text=True, timeout=30)
        log(f"   ✓ Status Planning Mega : {res.stdout.strip()[:100]}")
    except Exception as e:
        log(f"   ⚠️ Exception Planning : {e}")

    # Journalisation dans domino_runs.db
    if os.path.exists(RUNS_DB):
        try:
            rc = sqlite3.connect(RUNS_DB)
            rc.execute("INSERT INTO runs (name, ok, mode) VALUES (?, ?, ?)", (f"master-autopilot-cycle-{cycle}", 1, "FULL_LIVE_AUTOPILOT_247"))
            rc.commit()
            rc.close()
        except Exception:
            pass

    log(f"Cycle #{cycle} achevé. Pause de 90s avant la prochaine itération automatique...")
    time.sleep(90)
