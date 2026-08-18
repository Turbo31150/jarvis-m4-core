#!/usr/bin/env python3
"""
JARVIS OMEGA — Moteur d'Outreach Unifié AGY CLI + OpenClaw & BrowserOS CDP (M6 :9108 + Local :9222)
Gère l'automatisation directe des emails et de LinkedIn en utilisant AGY CLI (v1.1.8) et les agents conteneurisés.
"""
import os
import sys
import json
import time
import subprocess
from datetime import datetime

LOG_FILE = os.path.expanduser("~/jarvis/data/openclaw_agy_browseros_outreach.log")

def log(msg):
    txt = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(txt, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(txt + "\n")

log("🚀 DÉMARRAGE DU MOTEUR UNIFIÉ AGY CLI (v1.1.8) + OPENCLAW & BROWSEROS CDP (M6 :9108 + Local :9222)")

while True:
    try:
        # 1. Action Mail via AGY CLI & OpenClaw Conteneur
        log("📧 [AGY CLI & OPENCLAW MAIL] Exécution du triage & génération via AGY CLI...")
        cmd_agy_mail = "agy run 'Triage des mails IMAP et génération des réponses B2B' 2>&1"
        res_mail = subprocess.run(cmd_agy_mail, shell=True, capture_output=True, text=True, timeout=40)
        out_mail = res_mail.stdout.strip() if res_mail.stdout else res_mail.stderr.strip()
        log(f"   ✓ AGY CLI Mail Output : {out_mail[:120]}")

        # 2. Action LinkedIn via BrowserOS CDP (M6:9108 + Local:9222)
        log("💼 [BROWSEROS CDP LINKEDIN] Scan du feed, likes & commentaires sur BrowserOS (M6 :9108)...")
        cmd_browseros = "ssh -o ConnectTimeout=4 -o StrictHostKeyChecking=no turbo@10.42.0.230 'docker exec jarvis-linkedin-safe python3 /app/post.py --auto' 2>&1"
        res_browseros = subprocess.run(cmd_browseros, shell=True, capture_output=True, text=True, timeout=40)
        out_browseros = res_browseros.stdout.strip() if res_browseros.stdout else res_browseros.stderr.strip()
        log(f"   ✓ BrowserOS M6 Output : {out_browseros[:120]}")

        # 3. Action local dominos fallback avec --run LIVE
        log("⚡ [DOMINO LINKEDIN CDP LIVE] Exécution directe des actions sur le navigateur local :9222...")
        cmd_domino = "~/bin/dominos linkedin-realtime --run 2>&1"
        res_domino = subprocess.run(cmd_domino, shell=True, capture_output=True, text=True, timeout=40)
        out_domino = res_domino.stdout.strip() if res_domino.stdout else res_domino.stderr.strip()
        log(f"   ✓ Domino Live CDP Output : {out_domino[:120]}")

    except Exception as e:
        log(f"⚠️ Exception dans le moteur AGY/BrowserOS : {e}")

    log("⏳ Pause de 60s avant le prochain cycle d'action direct AGY/BrowserOS...")
    time.sleep(60)
