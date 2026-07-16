#!/usr/bin/env python3
"""Module Sauvegarde auto — snapshot des bases (ecole.db, notes.db) pour ne jamais
perdre le travail de la prof. Filet anti-perte demandé par l'audit.

- POST /api/backup      : crée un snapshot horodaté (rotation : garde les 10 derniers)
- GET  /api/backup/list : liste les sauvegardes disponibles

Appelé automatiquement par le front une fois par session (au chargement) + bouton
manuel. Léger, on-demand (aucun timer/daemon → 0 risque thermique, cf. règle du poste).
Sauvegarde le CODE-libre : uniquement des copies locales, jamais poussées (RGPD).
"""

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from flask import jsonify

BASE = Path(__file__).resolve().parent
BACKUP_DIR = BASE / "backups"
BASES = ["ecole.db", "notes.db"]
GARDER = 10  # rotation : nombre de snapshots conservés par base


def _snapshot(nom: str, stamp: str):
    """Copie cohérente d'une base SQLite via l'API backup (safe même en écriture)."""
    src = BASE / nom
    if not src.exists():
        return None
    BACKUP_DIR.mkdir(exist_ok=True)
    dst = BACKUP_DIR / f"{src.stem}-{stamp}.db"
    try:
        # sqlite backup API = copie cohérente même si la base est ouverte ailleurs
        con = sqlite3.connect(str(src))
        bck = sqlite3.connect(str(dst))
        with bck:
            con.backup(bck)
        con.close()
        bck.close()
    except sqlite3.Error:
        shutil.copy2(src, dst)  # repli : copie simple
    return dst


def _rotation(stem: str):
    """Ne garde que les GARDER snapshots les plus récents pour cette base."""
    snaps = sorted(BACKUP_DIR.glob(f"{stem}-*.db"), key=lambda p: p.name)
    for old in snaps[:-GARDER]:
        try:
            old.unlink()
        except OSError:
            pass


def register(app):
    try:
        from prof_routes import require_token
    except Exception:

        def require_token(f):
            return f

    @app.route("/api/backup", methods=["POST"])
    @require_token
    def api_backup():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        faits = []
        for nom in BASES:
            dst = _snapshot(nom, stamp)
            if dst:
                _rotation(Path(nom).stem)
                faits.append(
                    {
                        "base": nom,
                        "fichier": dst.name,
                        "ko": max(1, dst.stat().st_size // 1024),
                    }
                )
        if not faits:
            return jsonify({"ok": False, "error": "aucune base à sauvegarder"}), 404
        return jsonify({"ok": True, "stamp": stamp, "sauvegardes": faits})

    @app.route("/api/backup/list", methods=["GET"])
    @require_token
    def api_backup_list():
        if not BACKUP_DIR.exists():
            return jsonify({"ok": True, "backups": []})
        out = []
        for p in sorted(BACKUP_DIR.glob("*.db"), reverse=True)[:40]:
            out.append({"fichier": p.name, "ko": max(1, p.stat().st_size // 1024)})
        return jsonify({"ok": True, "backups": out})

    print("[autosave] module chargé (/api/backup, /api/backup/list)")
