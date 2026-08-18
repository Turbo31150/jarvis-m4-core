#!/usr/bin/env python3
"""
avale_remi_linux_tailscale.py — Aspiration Intégrale de Rémi Linux via Tailscale
Rôle :
  - Rapatrie les compétences, agents Claude, scripts JARVIS et bases de Rémi Linux (100.113.121.61)
  - Stocke le miroir complet sur /storage/remi-mirror/
  - Ingère immédiatement toutes les nouvelles connaissances dans board.db
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

TARGETS = [
    "skills-library",
    ".claude/agents",
    ".claude/skills",
    "jarvis-board",
    "jarvis-autonome",
    "claude-code-mastery",
    "jarvis/scripts",
    "jarvis/core",
    "jarvis/cli"
]

def log(msg):
    print(f"🌾 [AVALER-REMI] {msg}", flush=True)

def sync_target(target_rel):
    src = f"root@{REMI_IP}:/home/rempc/{target_rel}/"
    dst = STORAGE_REMI / target_rel
    dst.mkdir(parents=True, exist_ok=True)
    
    log(f"Rsync de [{target_rel}] depuis {REMI_IP} ...")
    cmd = [
        "rsync", "-avz", "--timeout=30",
        "-e", "tailscale ssh",
        src, str(dst) + "/"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if res.returncode == 0:
            log(f"  ✓ {target_rel} synchronisé avec succès.")
        else:
            log(f"  ℹ️ Sortie rsync ({target_rel}): {res.stderr.strip()[:150]}")
    except Exception as e:
        log(f"  ✗ Erreur rsync {target_rel}: {e}")

def ingest_harvested_skills():
    log("─── Ingestion des Compétences & Agents Rémi dans Board OS ───")
    ingest_script = BOARD_DIR / "ingest.py"
    if not ingest_script.exists():
        return

    skills_dir = STORAGE_REMI / "skills-library"
    if skills_dir.exists():
        cmd = [
            sys.executable, str(ingest_script),
            "--domain", "jarvis",
            "--path", str(skills_dir),
            "--title", "Skills Library Rémi Linux"
        ]
        subprocess.run(cmd, cwd=str(BOARD_DIR), capture_output=True, text=True)
        log("  ✓ Skills Library Rémi ingérée dans board.db")

    agents_dir = STORAGE_REMI / ".claude" / "agents"
    if agents_dir.exists():
        cmd = [
            sys.executable, str(ingest_script),
            "--domain", "jarvis",
            "--path", str(agents_dir),
            "--title", "Agents Claude Rémi Linux"
        ]
        subprocess.run(cmd, cwd=str(BOARD_DIR), capture_output=True, text=True)
        log("  ✓ Agents Claude Rémi ingérés dans board.db")

def main():
    start = time.time()
    log(f"🚀 DÉMARRAGE DE L'ASPIRATION TOTALE DE RÉMI LINUX ({REMI_IP})")
    
    for t in TARGETS:
        sync_target(t)

    ingest_harvested_skills()
    
    elapsed = time.time() - start
    log("=" * 70)
    log(f"🎉 RÉMI LINUX COMPLÈTEMENT AVALÉ & INGÉRÉ EN {elapsed:.1f}s")
    log(f"📍 Miroir local sécurisé : {STORAGE_REMI}")
    log("=" * 70)

if __name__ == "__main__":
    main()
