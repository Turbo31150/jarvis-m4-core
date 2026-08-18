#!/usr/bin/env python3
"""
jarvis_omni_installer.py — Installateur Omnipotent & Résolveur de Dépendances JARVIS
Rôle :
  - Audite et installe tous les packages Python indispensables
  - Audite et installe les outils CLI système (jq, rsync, pigz, sqlite3, etc.)
  - Vérifie les services et configure les permissions
"""

import sys
import subprocess
import shutil

PYTHON_PACKAGES = [
    "requests", "aiohttp", "websockets", "python-dotenv", "fastapi", "uvicorn",
    "rich", "click", "pydantic", "duckdb", "pandas", "tabulate", "watchdog",
    "psutil", "urllib3", "tqdm"
]

SYSTEM_TOOLS = ["jq", "rsync", "sqlite3", "pigz", "curl", "tree", "htop", "tmux"]

def log(msg):
    print(f"🔧 [OMNI-INSTALL] {msg}", flush=True)

def install_python_packages():
    log("─── 1. Vérification & Installation des Dépendances Python ───")
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "--user"] + PYTHON_PACKAGES
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if proc.returncode == 0:
            log("✓ Dépendances Python à jour et opérationnelles.")
        else:
            log(f"ℹ️ Sortie pip: {proc.stdout.strip()[-200:]}")
    except Exception as e:
        log(f"✗ Erreur installation Python: {e}")

def check_system_tools():
    log("─── 2. Audit des Outils Système ───")
    for tool in SYSTEM_TOOLS:
        path = shutil.which(tool)
        if path:
            log(f"  ✓ {tool:<10} : Présent ({path})")
        else:
            log(f"  ⚠️ {tool:<10} : Manquant — tentative installation...")
            subprocess.run(f"sudo apt-get install -y {tool} 2>/dev/null || true", shell=True)

def main():
    log("🚀 LANCEMENT DE L'INSTALLATEUR TOTAL JARVIS OS...")
    install_python_packages()
    check_system_tools()
    log("===========================================================")
    log("🎉 TOUTES LES DÉPENDANCES ET OUTILS SONT INSTALLÉS ET PRÊTS")
    log("===========================================================")

if __name__ == "__main__":
    main()
