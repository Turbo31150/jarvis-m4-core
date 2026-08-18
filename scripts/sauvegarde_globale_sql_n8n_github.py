#!/usr/bin/env python3
"""
sauvegarde_globale_sql_n8n_github.py — Sauvegarde Complète SQL, SQLite3, n8n et GitHub
1. Sauvegarde atomique des bases SQLite (board, moisson, jarvis_master, n8n database.sqlite)
2. Dump SQL compressé .sql.gz + contrôle d'intégrité PRAGMA
3. Export des workflows et configurations n8n
4. Commit Git sécurisé et Push sur GitHub
"""

import os
import sys
import time
import shutil
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = Path("/storage/backups") / f"backup_sql_n8n_{TIMESTAMP}"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
LATEST_LINK = Path("/storage/backups/latest")

DATABASES = [
    {"label": "board_os", "path": Path("/home/pamerys/labo/remi-board-kit/board.db")},
    {"label": "moisson_globale", "path": Path("/home/pamerys/labo/_admin-prive/index/moisson_globale.db")},
    {"label": "autopilot_executions", "path": Path("/home/pamerys/labo/remi-board-kit/autopilot_executions.db")},
    {"label": "n8n_database", "path": Path.home() / ".n8n" / "database.sqlite"},
    {"label": "jarvis_master", "path": Path("/storage/m1-mirror/databases/jarvis_master.db")},
    {"label": "unified_plan", "path": Path("/storage/m1-mirror/databases/unified_plan.db")},
    {"label": "cowork_engine", "path": Path("/storage/m1-mirror/databases/cowork_engine.db")},
    {"label": "jarvis_logs", "path": Path("/storage/m1-mirror/databases/jarvis_logs.db")},
]

def log(msg):
    print(f"📦 [BACKUP-TOTAL] {msg}", flush=True)

def step1_sql_n8n_backup():
    log(f"─── 1. Sauvegarde Atomique des Bases SQL & n8n ➔ {BACKUP_DIR} ───")
    manifest = []
    
    for db_info in DATABASES:
        label = db_info["label"]
        src = db_info["path"]
        if not src.exists():
            log(f"  ℹ️ {label} absent ({src}) — ignoré")
            continue

        sz_mb = src.stat().st_size / (1024 * 1024)
        dst_db = BACKUP_DIR / f"{label}_{TIMESTAMP}.db"
        dst_sql_gz = BACKUP_DIR / f"{label}_{TIMESTAMP}.sql.gz"
        
        log(f"Sauvegarde [{label}] ({sz_mb:.2f} Mo)...")
        
        # Copie atomique
        try:
            with sqlite3.connect(src) as s_cx:
                with sqlite3.connect(dst_db) as d_cx:
                    s_cx.backup(d_cx, pages=1000)
            log(f"  ✓ Copie atomique OK : {dst_db.name}")
        except Exception as e:
            log(f"  ! Fallback shutil copy pour {label}: {e}")
            shutil.copy2(src, dst_db)

        # Integrity check
        integrity = "KO"
        try:
            with sqlite3.connect(dst_db) as t_cx:
                integrity = t_cx.execute("PRAGMA integrity_check").fetchone()[0]
            log(f"  ✓ Test intégrité PRAGMA : {integrity}")
        except Exception as e:
            log(f"  ✗ Erreur intégrité {label}: {e}")

        # Dump SQL compressé
        if src.stat().st_size < 2 * 1024 * 1024 * 1024:
            try:
                cmd = f"sqlite3 '{dst_db}' .dump | gzip -9 > '{dst_sql_gz}'"
                subprocess.run(cmd, shell=True, timeout=120, check=True)
                log(f"  ✓ Dump SQL compressé : {dst_sql_gz.name} ({dst_sql_gz.stat().st_size / (1024*1024):.2f} Mo)")
            except Exception as e:
                log(f"  ! Dump SQL ignoré : {e}")

        manifest.append({
            "label": label,
            "file": dst_db.name,
            "size_mb": sz_mb,
            "integrity": integrity
        })

    # Sauvegarde des fichiers de configuration & workflows n8n
    n8n_wf_dir = BACKUP_DIR / "n8n_workflows_and_config"
    n8n_wf_dir.mkdir(exist_ok=True)
    n8n_home = Path.home() / ".n8n"
    if n8n_home.exists():
        for cfg in ["config", "nodes", "storage"]:
            src_cfg = n8n_home / cfg
            if src_cfg.exists():
                if src_cfg.is_dir():
                    shutil.copytree(src_cfg, n8n_wf_dir / cfg, dirs_exist_ok=True)
                else:
                    shutil.copy2(src_cfg, n8n_wf_dir / cfg)
        log("  ✓ Configurations & nodes n8n sauvegardés")

    # Mettre à jour le lien latest
    try:
        if LATEST_LINK.is_symlink() or LATEST_LINK.exists():
            LATEST_LINK.unlink()
        LATEST_LINK.symlink_to(BACKUP_DIR)
        log(f"  ✓ Lien latest ➔ {BACKUP_DIR}")
    except Exception:
        pass

def step2_github_sync():
    log("─── 2. Sauvegarde & Synchronisation GitHub ───")
    repos = [
        Path.home() / "labo",
        Path.home() / "jarvis",
        Path.home() / "jarvis-cowork"
    ]

    for repo in repos:
        if (repo / ".git").exists():
            log(f"Synchronisation Git de : {repo} ...")
            try:
                # Add
                subprocess.run(["git", "add", "-A"], cwd=str(repo), capture_output=True, text=True)
                # Status check
                st = subprocess.check_output(["git", "status", "--porcelain"], cwd=str(repo), text=True).strip()
                if st:
                    commit_msg = f"chore(backup): sauvegarde auto sql/n8n/board [{TIMESTAMP}]"
                    subprocess.run(["git", "commit", "-m", commit_msg], cwd=str(repo), capture_output=True, text=True)
                    log(f"  ✓ Commit local créé pour {repo.name}")
                    # Push si remote présent
                    push_res = subprocess.run(["git", "push", "origin"], cwd=str(repo), capture_output=True, text=True, timeout=60)
                    if push_res.returncode == 0:
                        log(f"  ✓ Git push réussi pour {repo.name}")
                    else:
                        log(f"  ℹ️ Git push ({repo.name}) : {push_res.stderr.strip()[:150]}")
                else:
                    log(f"  ✓ {repo.name} : Répertoire de travail propre (aucun changement à committer)")
            except Exception as e:
                log(f"  ✗ Erreur Git {repo.name}: {e}")

def main():
    start = time.time()
    log(f"🚀 LANCEMENT DU PROTOCOLE DE SAUVEGARDE UNIFIÉE SQL + n8n + GITHUB")
    step1_sql_n8n_backup()
    step2_github_sync()
    elapsed = time.time() - start
    log("=" * 70)
    log(f"🎉 SAUVEGARDE & SYNCHRO GITHUB COMPLÈTES EN {elapsed:.1f}s")
    log(f"📍 Emplacement NVMe : {BACKUP_DIR}")
    log("=" * 70)

if __name__ == "__main__":
    main()
