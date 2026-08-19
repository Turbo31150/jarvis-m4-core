#!/usr/bin/env python3
"""
JARVIS-OMEGA — Claude Code Extension & BrowserOS Dispatcher
===========================================================
Génère et transmet des ordres de mission structurés à Claude Code CLI
avec instructions complètes de publication et commentaires LinkedIn via BrowserOS.
"""

import os
import sys
import json
import sqlite3
import datetime
import subprocess
from pathlib import Path

DB_MASTER = Path("/home/pamerys/jarvis/jarvis_master.db")
CLAUDE_BIN = "/home/pamerys/.local/bin/claude"
BROWSEROS_URL = "http://127.0.0.1:9108"

def get_next_mission_payload():
    with sqlite3.connect(str(DB_MASTER), timeout=8) as cx:
        cx.row_factory = sqlite3.Row
        row = cx.execute("""
            SELECT id, theme, hook, content, target_audience
            FROM linkedin_content_stream 
            WHERE status IN ('READY', 'QUEUED') 
            ORDER BY id ASC LIMIT 1
        """).fetchone()
        
        if row:
            return dict(row)
            
    return {
        "id": 999,
        "theme": "Architecture Multi-Agents Souveraine 2026",
        "hook": "Comment faire tourner 12 agents IA autonomes en production sans saturer la RAM ni dépendre du Cloud US.",
        "content": "Déploiement On-Premise avec inférence 0 ms, SQLite WAL et lien direct 1.3 ms.",
        "target_audience": "DSI & Directeurs R&D"
    }

def dispatch_to_claude_extension():
    mission = get_next_mission_payload()
    post_id = mission.get("id")
    theme = mission.get("theme")
    hook = mission.get("hook")
    audience = mission.get("target_audience")
    
    print("==================================================================")
    print("🤖 [DISPATCHER CLAUDE CODE & EXTENSION] TRANSMISSION D'ORDRE")
    print(f"🎯 Mission #{post_id} : {theme}")
    print("==================================================================")
    
    instruction = f"""Tu es l'agent autonome d'exécution JARVIS OS pour Franck Delmas.
MISSION DE PUBLICATION LINKEDIN :
- Cible : {audience}
- Thème : {theme}
- Accroche : {hook}

TÂCHES À RÉALISER :
1. Rédige un post d'autorité complet (Hook, Problème Cloud US/NIS2, Solution JARVIS OS On-Premise, CTA, Hashtags).
2. Rédige un commentaire technique d'accompagnement.
3. Valide que l'ordre est prêt pour injection BrowserOS (Port 9108).

Réponds sous forme de JSON structuré :
{{
  "post_text": "...",
  "comment_text": "...",
  "status": "READY_FOR_BROWSEROS"
}}"""

    print("📤 Envoi du cahier des charges à Claude Code...")
    try:
        res = subprocess.run([CLAUDE_BIN, "-p", instruction], capture_output=True, text=True, timeout=8)
        output = res.stdout.strip()
        print(f"📥 Réponse reçue de Claude Code ({len(output)} caractères)")
    except Exception as e:
        print(f"⚠️ Erreur ou timeout Claude Code: {e}")

    # Exécution de publication via le pont BrowserOS
    print("🚀 Déclenchement automatique de l'injection BrowserOS...")
    with open("/home/pamerys/jarvis/logs/browseros_poster.log", "a", encoding="utf-8") as log_f:
        subprocess.run(["python3", "/home/pamerys/jarvis/scripts/jarvis_browseros_claudecode_poster.py"], stdout=log_f, stderr=log_f)
    
    # Nettoyage Zéro-Déchet
    os.system("rm -f /tmp/*.png /tmp/*.xml /tmp/*.3gp /tmp/*.wav /tmp/*.mp3 2>/dev/null")
    print("🧹 Système nettoyé et purgé.")

if __name__ == "__main__":
    dispatch_to_claude_extension()
