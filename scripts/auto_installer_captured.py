#!/usr/bin/env python3
"""
auto_installer_captured.py — Auto-installer des projets GitHub capturés
Clone automatiquement les dépôts découverts sur le web dans /home/pamerys/Workspaces/scraped_projects
"""

import sqlite3
import os
import subprocess

DEST_DIR = os.path.expanduser("~/Workspaces/scraped_projects")
os.makedirs(DEST_DIR, exist_ok=True)

DB_PATH = os.path.expanduser("~/jarvis/jarvis_master.db")


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        "SELECT path, title FROM biblio_knowledge WHERE domain = 'GitHub' ORDER BY id DESC LIMIT 30"
    )
    repos = cur.fetchall()

    print(f"[Auto-Installer] {len(repos)} dépôts GitHub récents vérifiés...")

    from urllib.parse import (
        urlparse,
    )  # A0 : path = contenu scrapé non fiable → validation stricte

    for path, title in repos:
        # Validation stricte AVANT git (anti argument/command injection) :
        # https uniquement, hostname EXACT github.com (pas substring), pas de flag en tête.
        try:
            u = urlparse(path.strip())
        except Exception:
            continue
        if (
            u.scheme != "https"
            or u.hostname != "github.com"
            or path.strip().startswith("-")
        ):
            print(f"[Skip] URL non fiable rejetée: {path}")
            continue
        repo_name = os.path.basename(u.path.rstrip("/"))
        if not repo_name or repo_name.startswith("-"):
            continue
        target_path = os.path.join(DEST_DIR, repo_name)
        if not os.path.exists(target_path):
            print(f"[Cloning] {title} -> {path}")
            try:
                env = {**os.environ, "GIT_ALLOW_PROTOCOL": "https"}
                subprocess.run(
                    [
                        "git",
                        "-c",
                        "protocol.ext.allow=never",
                        "clone",
                        "--depth",
                        "1",
                        "--",
                        path.strip(),
                        target_path,
                    ],
                    check=True,
                    timeout=60,
                    env=env,
                )
                print(f"[Installed] ✅ {repo_name} dans {target_path}")
            except Exception as e:
                print(f"[Error] Échec du clonage {path}: {e}")
        else:
            print(f"[Exists] ⏩ {repo_name} déjà présent.")


if __name__ == "__main__":
    main()
