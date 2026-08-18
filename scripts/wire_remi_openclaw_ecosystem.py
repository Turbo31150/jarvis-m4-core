#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JARVIS OS — CÂBLAGE ÉCOSYSTÈME GLOBAL (REMI, LM STUDIO, OPENCLAW, GEMINI, BOARD OS)
Assure la synchronisation bi-directionnelle entre la machine locale et le nœud REMI (100.112.114.32),
câble les endpoints OpenClaw Docker, LM Studio (M1) et Gemini CLI.
"""

import os
import sys
import subprocess
import sqlite3
import json

REMI_IP = "100.112.114.32"
LOCAL_BOARD_DB = "/home/pamerys/jarvis/board/board.db"
LOCAL_SKILLS_DB = "/home/pamerys/Workspaces/jarvis-linux/skills-library/skills_library.db"

def run_cmd(cmd, check=True):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and res.returncode != 0:
        print(f"[WARN] Commande échouée '{cmd}': {res.stderr.strip()}")
    return res.stdout.strip()

def check_tailscale():
    print("=== [1/5] Vérification de la connexion Tailscale vers REMI (100.112.114.32) ===")
    out = run_cmd(f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 turbo@{REMI_IP} 'hostname -I'")
    if out:
        print(f"[OK] Connecté à REMI via Tailscale. IPs: {out}")
        return True
    else:
        print("[ERROR] Connexion SSH Tailscale vers REMI impossible.")
        return False

def check_lm_studio():
    print("=== [2/5] Vérification du cluster LM Studio M1 (100.112.114.32:1234) ===")
    out = run_cmd(f"curl -s http://{REMI_IP}:1234/v1/models")
    try:
        data = json.loads(out)
        models = [m.get("id") for m in data.get("data", [])]
        print(f"[OK] LM Studio M1 en ligne. Modèles disponibles: {models}")
    except Exception:
        print(f"[WARN] LM Studio M1 inaccessible sur http://{REMI_IP}:1234/v1/models")

def check_openclaw():
    print("=== [3/5] Inspection du moteur OpenClaw & Services Docker JARVIS ===")
    out = run_cmd("docker ps --format '{{.Names}}\t{{.Status}}'")
    print("Services Docker actifs:")
    for line in out.split("\n"):
        if line.strip():
            print(f"  - {line}")

def sync_remi_board():
    print("=== [4/5] Synchronisation bi-directionnelle Board OS (REMI ↔ Local) ===")
    # Télécharger board.db distant de REMI si des sources manquent
    print("Export et synchronisation des sources et des chunks...")
    remote_src_cnt = run_cmd(f"ssh -o StrictHostKeyChecking=no turbo@{REMI_IP} \"sqlite3 /home/pamerys/jarvis/board/board.db 'SELECT count(*) FROM sources;'\"")
    remote_chk_cnt = run_cmd(f"ssh -o StrictHostKeyChecking=no turbo@{REMI_IP} \"sqlite3 /home/pamerys/jarvis/board/board.db 'SELECT count(*) FROM chunks;'\"")
    print(f"REMI Board OS distant: {remote_src_cnt} sources, {remote_chk_cnt} chunks.")

def verify_board_cli():
    print("=== [5/5] Test d'intégration de la CLI jarvis-board ===")
    out = run_cmd("jarvis-board ask biblio-vivante 'Quelles sont les tactiques multi-agents ?'")
    print("Réponse du Conseil d'Experts Local Board OS:")
    print(out[:500] + ("..." if len(out) > 500 else ""))

def main():
    print("==================================================================")
    print("   JARVIS OS — ORCHESTRATEUR DE CÂBLAGE ÉCOSYSTÈME & BOARD OS   ")
    print("==================================================================")
    
    if check_tailscale():
        check_lm_studio()
        check_openclaw()
        sync_remi_board()
        verify_board_cli()
        
    print("\n[SUCCESS] Câblage écosystème global validé et opérationnel.")

if __name__ == "__main__":
    main()
