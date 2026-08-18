#!/usr/bin/env python3
"""
dispatch_table_ronde.py — Distribution des tâches du Board & Débat Table Ronde des 7 Experts.
0 Token payant.
Prend une tâche du Planning/To-Do List, la soumet aux experts du domaine,
synthétise le consensus et journalise la décision dans jarvis_master.db.
"""

from __future__ import annotations
import argparse
import json
import sqlite3
import subprocess
import sys
import os
from pathlib import Path

HOME = Path.home()
BOARD_DIR = HOME / "jarvis/board"
MASTER_DB = HOME / "jarvis/jarvis_master.db"

EXPERTS = [
    {"id": "archi", "name": "Architecte Système & Cluster", "lens": "Pérennité, modularité, 0-dette, topologie M4/M6/SSD"},
    {"id": "code", "name": "Ingénieur Core Python & Dev", "lens": "Typage strict, tests unitaires, performance, lisibilité"},
    {"id": "sec", "name": "Expert Sécurité & Sandboxing", "lens": "Zero-trust, étanchéité des conteneurs, protection des credentials"},
    {"id": "finops", "name": "Arbitre FinOps & 0-Token", "lens": "Priorité absolue aux calculs locaux déterministes et inférence GPU M6"},
    {"id": "data", "name": "Ingénieur Data & Bases SQL", "lens": "Postgres Swarm, Redis, SQLite WAL, cohérence FTS5"},
    {"id": "ops", "name": "Orchestrateur Docker & Swarm", "lens": "Haute disponibilité des services, redémarrage auto, ports"},
    {"id": "biz", "name": "Stratège Business & Contenu", "lens": "Impact utilisateur, prospection réelle, valeur ajoutée"}
]

def get_pending_tasks(limit=10):
    if not MASTER_DB.exists():
        return []
    try:
        con = sqlite3.connect(MASTER_DB)
        cur = con.cursor()
        cur.execute("SELECT id, title, status, category FROM tasks WHERE status='PENDING' ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        con.close()
        return [{"id": r[0], "title": r[1], "status": r[2], "category": r[3]} for r in rows]
    except Exception as e:
        return []

def consult_table_ronde(task_title: str, domain: str = "system") -> str:
    print(f"🏛 [TABLE RONDE] Débat des 7 Experts sur la tâche : '{task_title}'")
    try:
        # 2026-08-18 — le timeout etait de 45 s alors qu'un vrai debat du board
        # prend 100 a 300 s (4-5 experts sequentiels + arbitre, mesure). Le timeout
        # tombait donc a CHAQUE appel, et le repli ci-dessous s'affichait sous le
        # titre « SYNTHESE DE LA TABLE RONDE ... Consensus atteint » : un faux
        # consensus, indistinguable d'une vraie deliberation. Un debat qui echoue
        # doit le DIRE, jamais inventer un accord que personne n'a exprime.
        cmd = ["python3", str(BOARD_DIR / "board.py"), "ask", domain, task_title]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout
        return ("⚠ TABLE RONDE SANS VERDICT — board.py ask a rendu "
                f"rc={r.returncode} sans sortie exploitable.\n"
                f"   stderr : {(r.stderr or '(vide)').strip()[:400]}\n"
                "   Aucun consensus n'est rapporte : il n'y a pas eu de debat.")
    except subprocess.TimeoutExpired:
        return ("⚠ TABLE RONDE INTERROMPUE — le board n'a pas rendu son arbitrage "
                "dans le delai imparti (600 s).\n"
                "   Aucun consensus n'est rapporte : le debat n'est pas alle a son terme.\n"
                "   Verifier le backend chat : curl -s $BOARD_LMS_URL/models")
    except Exception as e:
        return (f"⚠ TABLE RONDE INDISPONIBLE — {type(e).__name__}: {e}\n"
                "   Aucun consensus n'est rapporte.")

def main():
    parser = argparse.ArgumentParser(description="Distribution Table Ronde & Board Planning")
    parser.add_argument("--task", type=str, help="Titre de la tâche à arbitrer")
    parser.add_argument("--list", action="store_true", help="Lister les tâches en attente du planning")
    parser.add_argument("--domain", type=str, default="system", help="Domaine d'expertise")
    args = parser.parse_args()

    if args.list:
        tasks = get_pending_tasks()
        print(f"📋 {len(tasks)} Tâches PENDING dans le Planning Unified :")
        for t in tasks:
            print(f"  • [#{t['id']}] ({t['category']}) {t['title']}")
        return

    task_title = args.task or "Alignement et synchronisation globale des agents JARVIS"
    res = consult_table_ronde(task_title, args.domain)
    print(res)

if __name__ == "__main__":
    main()
