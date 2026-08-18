#!/usr/bin/env python3
"""
harvest_all_remi_nodes.py — Aspiration Intégrale Haute Vitesse de Rémi Linux via Tar Streaming
Rôle :
  - Aspire en flux compressé continu (tar | tar) via Tailscale SSH root
  - Copie l'intégralité des agents, compétences, codes et configurations de Rémi Linux
  - Ingère tout le savoir extrait dans board.db (RAG 768D)
"""

import os
import sys
import time
import subprocess
from pathlib import Path

REMI_IP = "100.113.121.61"
STORAGE_REMI = Path("/storage/remi-mirror")
STORAGE_REMI.mkdir(parents=True, exist_ok=True)
BOARD_DIR = Path.home() / "labo" / "remi-board-kit"

TARGET_FOLDERS = [
    "skills-library",
    ".claude",
    "claude-code-mastery",
    "jarvis-board",
    "jarvis-autonome",
    "jarvis-audit",
    "jarvis-benchmark",
    "jarvis/scripts",
    "jarvis/core",
    "jarvis/cli"
]

def log(msg):
    print(f"🌊 [ASPIRER-REMI] {msg}", flush=True)

def stream_pull_folder(folder_rel):
    log(f"Aspiration en streaming de [{folder_rel}] ...")
    cmd = f"tailscale ssh root@{REMI_IP} 'tar -czf - -C /home/rempc/ \"{folder_rel}\" 2>/dev/null' | tar -xzf - -C /storage/remi-mirror/ 2>/dev/null"
    try:
        res = subprocess.run(cmd, shell=True, timeout=600)
        if res.returncode == 0:
            log(f"  ✓ [{folder_rel}] extrait avec succès sur /storage/remi-mirror/")
        else:
            log(f"  ℹ️ Code retour [{folder_rel}]: {res.returncode}")
    except Exception as e:
        log(f"  ✗ Erreur sur [{folder_rel}]: {e}")

def ingest_all_to_board():
    log("─── Ingestion Complète dans Board OS (board.db) ───")
    ingest_script = BOARD_DIR / "ingest.py"
    if not ingest_script.exists():
        return

    # Ingestion skills & agents
    dirs_to_ingest = [
        (STORAGE_REMI / "skills-library", "Skills Library Rémi"),
        (STORAGE_REMI / ".claude" / "agents", "Agents Claude Rémi"),
        (STORAGE_REMI / "claude-code-mastery", "Claude Code Mastery Rémi"),
        (STORAGE_REMI / "jarvis-board", "Board Scripts Rémi"),
        (STORAGE_REMI / "jarvis-autonome", "Autonome Engine Rémi")
    ]

    for p, title in dirs_to_ingest:
        if p.exists():
            log(f"Ingestion de [{title}] ...")
            cmd = [
                sys.executable, str(ingest_script),
                "--domain", "jarvis",
                "--path", str(p),
                "--title", title
            ]
            try:
                subprocess.run(cmd, cwd=str(BOARD_DIR), capture_output=True, text=True, timeout=1200)
                log(f"  ✓ {title} indexé dans board.db")
            except Exception as err:
                log(f"  ⚠ Erreur ingestion {title}: {err}")

def main():
    start = time.time()
    log(f"🚀 LANCEMENT DE L'ASPIRATION TOTALE DE RÉMI LINUX ({REMI_IP})")
    
    for f in TARGET_FOLDERS:
        stream_pull_folder(f)

    ingest_all_to_board()
    
    elapsed = time.time() - start
    log("=" * 70)
    log(f"🎉 ASPIRATION TOTALE TERMINÉE EN {elapsed:.1f}s")
    log(f"📁 Données hébergées sur : {STORAGE_REMI}")
    log("=" * 70)

if __name__ == "__main__":
    main()
