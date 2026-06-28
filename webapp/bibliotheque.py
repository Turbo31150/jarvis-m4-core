#!/usr/bin/env python3
"""Module Bibliothèque — commandes & skills par mots-clés.

Expose en lecture seule la base d'index ~/jarvis/stacks/jarvis-index.db
(tables commands / skills / employees / services) dans l'app Espace Prof.
register(app) branche /api/biblio sur le Flask existant. Réversible :
supprimer l'import dans server.py suffit.
"""

import sqlite3
from pathlib import Path
from flask import jsonify, request

DB = Path("/home/pamerys/jarvis/stacks/jarvis-index.db")


def _q(sql, args=()):
    """Requête lecture seule sur la base d'index ; [] si table/base absente."""
    if not DB.exists():
        return []
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute(sql, args).fetchall()]
    except sqlite3.Error:
        return []
    finally:
        con.close()


def register(app):
    # Protéger comme les routes prof (le serveur écoute sur 0.0.0.0) ; localhost reste exempté.
    try:
        from prof_routes import require_token
    except Exception:

        def require_token(f):
            return f

    @app.route("/api/biblio")
    @require_token
    def api_biblio():
        q = (request.args.get("q") or "").strip()[:60]
        if q:
            like = f"%{q}%"
            cmds = _q(
                "SELECT entity,label,command,description FROM commands "
                "WHERE label LIKE ? OR command LIKE ? OR description LIKE ? OR entity LIKE ? "
                "ORDER BY entity,label LIMIT 120",
                (like, like, like, like),
            )
            sk = _q(
                "SELECT entity,skill,role,keywords FROM skills "
                "WHERE skill LIKE ? OR keywords LIKE ? OR role LIKE ? ORDER BY skill LIMIT 60",
                (like, like, like),
            )
        else:
            cmds = _q(
                "SELECT entity,label,command,description FROM commands ORDER BY entity,label"
            )
            sk = _q("SELECT entity,skill,role,keywords FROM skills ORDER BY skill")
        stats = {
            "commands": len(_q("SELECT 1 FROM commands")),
            "skills": len(_q("SELECT 1 FROM skills")),
            "employees": len(_q("SELECT 1 FROM employees")),
        }
        return jsonify(
            {"ok": True, "q": q, "commands": cmds, "skills": sk, "stats": stats}
        )

    print("[bibliotheque] module chargé (/api/biblio)")
