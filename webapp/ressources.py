# -*- coding: utf-8 -*-
"""Module Ressources — sert les supports pédagogiques imprimables (PDF) depuis l'app.
Pattern modulaire register(app). Sécurisé contre le path traversal."""

import os
from pathlib import Path

from flask import jsonify, send_from_directory, abort

_HERE = Path(__file__).resolve().parent
_BASE = _HERE / "static" / "prof"  # racine autorisée des ressources


def _human(n: int) -> str:
    for unit in ("o", "Ko", "Mo"):
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.0f} Go"


def _scan():
    """Liste les ressources (PDF en priorité) groupées par dossier thématique."""
    out = []
    if not _BASE.exists():
        return out
    for root, _dirs, files in os.walk(_BASE):
        rel_dir = Path(root).relative_to(_BASE)
        for f in sorted(files):
            if not f.lower().endswith((".pdf", ".md", ".wav")):
                continue
            full = Path(root) / f
            rel = (rel_dir / f).as_posix()
            out.append(
                {
                    "nom": f,
                    "theme": rel_dir.parts[0] if rel_dir.parts else "general",
                    "type": f.rsplit(".", 1)[-1].lower(),
                    "taille": _human(full.stat().st_size),
                    "url": f"/ressources/{rel}",
                }
            )
    # PDF d'abord, puis md, puis wav
    order = {"pdf": 0, "md": 1, "wav": 2}
    out.sort(key=lambda r: (r["theme"], order.get(r["type"], 9), r["nom"]))
    return out


def register(app):
    @app.route("/api/prof/ressources")
    def _list_ressources():
        return jsonify({"ressources": _scan()})

    @app.route("/api/prof/ressources-externes")
    def _list_externes():
        import json

        f = _BASE / "ressources-libres.json"
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            data = []
        return jsonify({"externes": data})

    @app.route("/ressources/<path:relpath>")
    def _get_ressource(relpath):
        # sécurisation: le chemin résolu doit rester sous _BASE
        target = (_BASE / relpath).resolve()
        try:
            target.relative_to(_BASE)
        except ValueError:
            abort(403)
        if not target.is_file():
            abort(404)
        return send_from_directory(target.parent, target.name)

    print("[JARVIS] Ressources chargé (/api/prof/ressources, /ressources/<...>)")
