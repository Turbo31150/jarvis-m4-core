#!/usr/bin/env python3
"""
JARVIS OMEGA — Autopilot Permanent Présence LinkedIn (Live 24/7)
1. Scrute le fil d'actualité en continu via Chrome CDP (:9222).
2. Analyse les publications récentes et commente avec des réponses techniques/IA.
3. Rédige et publie des posts viraux B2B & IA.
4. Effectue de l'outreach et prend contact avec les décideurs.
"""
import time
import os
import sys
import subprocess
import json
from datetime import datetime

LOG_FILE = os.path.expanduser("~/jarvis/data/linkedin_autopilot_permanent.log")

def log(msg):
    txt = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(txt, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(txt + "\n")

log("🚀 DÉMARRAGE DU PILOTE AUTOMATIQUE PERMANENT LINKEDIN 24/7")

while True:
    try:
        log("🔍 [1/3] Lecture du fil d'actualités, détection de posts & réactions (likes/commentaires)...")
        cmd_feed = "/home/pamerys/jarvis/bin/dominos linkedin-realtime --run 2>&1"
        res = subprocess.run(cmd_feed, shell=True, capture_output=True, text=True, timeout=60)
        out = res.stdout.strip() if res.stdout else res.stderr.strip()
        log(f"   ✓ Engagement Feed Status : {out[:120]}")

        log("✍️ [2/3] Génération & Publication de contenu B2B IA...")
        cmd_post = "/home/pamerys/jarvis/bin/dominos linkedin-post-auto --run 2>&1"
        res_post = subprocess.run(cmd_post, shell=True, capture_output=True, text=True, timeout=60)
        out_post = res_post.stdout.strip() if res_post.stdout else res_post.stderr.strip()
        log(f"   ✓ Publication Post Status : {out_post[:120]}")

        log("🤝 [3/3] Prise de contact directe (Outreach Décideurs & Entreprises)...")
        cmd_outreach = "/home/pamerys/jarvis/bin/dominos linkedin-dm-sequence --run 2>&1"
        res_out = subprocess.run(cmd_outreach, shell=True, capture_output=True, text=True, timeout=60)
        out_out = res_out.stdout.strip() if res_out.stdout else res_out.stderr.strip()
        log(f"   ✓ Outreach Direct Status : {out_out[:120]}")

    except Exception as e:
        log(f"⚠️ Exception dans le cycle LinkedIn 24/7 : {e}")

    log("⏳ Attente 120s avant le prochain cycle d'engagement permanent...")
    time.sleep(120)
