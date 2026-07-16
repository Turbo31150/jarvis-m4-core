#!/usr/bin/env python3
"""Module Supports — met TOUT dans l'application : expose les modèles admin (JSON)
et sert les supports HTML générés (recueils, classeur de modèles, plans de l'année)
sous une page d'accueil unique /supports. Branché par server.py via register(app)."""

import sqlite3
from pathlib import Path
from flask import jsonify, send_from_directory, abort, request

BASE = Path(__file__).resolve().parent
DB = BASE / "ecole.db"
STATIC = BASE / "static"
DOSSIERS = {
    "recueils": "📚 Recueils de fiches (par niveau)",
    "plans": "🗓️ Plans de l'année (MS/GS × 5 périodes)",
    "modeles": "🗂️ Classeur de modèles (mails, réunions, absences…)",
}


def _accueil_html():
    cartes = []
    for d, titre in DOSSIERS.items():
        dossier = STATIC / d
        fichiers = sorted(dossier.glob("*.html")) if dossier.exists() else []
        liens = "".join(
            f'<a href="/supports/{d}/{f.name}">{f.stem.replace("recueil-", "").replace("plan-", "")}</a>'
            for f in fichiers
            if f.name != "index.html"
        )
        idx = (
            f'<a class="idx" href="/supports/{d}/index.html">▸ tout ouvrir</a>'
            if (dossier / "index.html").exists()
            else ""
        )
        cartes.append(
            f'<section><h2>{titre}</h2><div class="g">{liens}</div>{idx}</section>'
        )
    css = (
        "body{font-family:system-ui,sans-serif;max-width:900px;margin:auto;padding:28px;background:#f7f5ef;color:#222}"
        "h1{color:#1a6a4a}h2{color:#1a6a4a;font-size:17px;margin-top:22px}"
        ".g{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}"
        "a{padding:8px 12px;background:#fff;border:1px solid #e0ddd4;border-radius:8px;text-decoration:none;color:#1a6a4a;font-size:13px}"
        "a:hover{border-color:#1a6a4a}a.idx{background:#1a6a4a;color:#fff;font-weight:600}"
    )
    return (
        f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Supports — Pousseline</title>'
        f"<style>{css}</style></head><body><h1>📎 Tous tes supports</h1>"
        f"<p>Recueils imprimables, classeur de modèles et plans de l'année — tout au même endroit. Ctrl+P pour imprimer.</p>"
        f"{''.join(cartes)}</body></html>"
    )


def register(app):
    @app.route("/api/modeles")
    def api_modeles():
        cat = request.args.get("cat")
        q = request.args.get("q")
        c = sqlite3.connect(DB)
        c.row_factory = sqlite3.Row
        sql = "SELECT id,categorie,titre,corps FROM modeles WHERE 1=1"
        a = []
        if cat:
            sql += " AND categorie=?"
            a.append(cat)
        if q:
            sql += " AND (titre LIKE ? OR corps LIKE ?)"
            a += [f"%{q}%", f"%{q}%"]
        sql += " ORDER BY categorie, titre"
        rows = [dict(r) for r in c.execute(sql, a)]
        c.close()
        return jsonify(rows)

    @app.route("/supports")
    def supports_home():
        return _accueil_html()

    @app.route("/supports/<path:sub>")
    def supports_file(sub):
        # sécurité : uniquement les dossiers de supports connus, pas de traversée
        parts = sub.split("/")
        if len(parts) != 2 or parts[0] not in DOSSIERS or ".." in sub:
            abort(404)
        d = STATIC / parts[0]
        if not (d / parts[1]).exists():
            abort(404)
        return send_from_directory(str(d), parts[1])

    print("[supports] chargé (/api/modeles, /supports, /supports/<dossier>/<fichier>)")
