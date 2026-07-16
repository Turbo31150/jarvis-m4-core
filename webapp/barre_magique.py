# -*- coding: utf-8 -*-
"""Barre magique — routeur par mot-clé (0 token).

Tu écris une phrase → détection via la bibliothèque SQL `kb_keywords` (aucune
inférence) → intent + route + params extraits du contexte. Le front n'a plus qu'à
exécuter la route détectée. Principe : la structure est déjà en place, on ne fait
qu'adapter les paramètres au contexte.
Branché par server.py via register(app).
"""

import re
import sqlite3
from pathlib import Path

from flask import jsonify, request

ECOLE_DB = Path(__file__).resolve().parent / "ecole.db"

NIVEAUX = ["PS", "MS", "GS", "CP", "CE1", "CE2", "CM1", "CM2"]
MATIERES = [
    "maths",
    "mathématiques",
    "français",
    "lecture",
    "phono",
    "phonologie",
    "graphisme",
    "écriture",
    "langage",
    "nombres",
    "formes",
    "arts",
    "motricité",
    "questionner le monde",
    "sciences",
    "histoire",
    "géographie",
]
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi"]


def _conn():
    c = sqlite3.connect(str(ECOLE_DB))
    c.row_factory = sqlite3.Row
    return c


def _detect(phrase):
    """Détecte l'intention + les paramètres. 0 token : SQL + regex uniquement."""
    p = phrase.lower().strip()
    rows = (
        _conn()
        .execute(
            "SELECT intent, route, methode, mots_cles, exemple, params_hint FROM kb_keywords"
        )
        .fetchall()
    )
    best, best_score = None, 0
    for r in rows:
        hits = sum(1 for m in r["mots_cles"].split(",") if m.strip() and m.strip() in p)
        if hits > best_score:
            best, best_score = r, hits
    if not best:
        return None
    # Extraction des paramètres depuis le contexte de la phrase
    params = {}
    for niv in NIVEAUX:
        if re.search(r"\b" + niv.lower() + r"\b", p):
            params["niveau"] = niv
            break
    for m in MATIERES:
        if m in p:
            params["matiere"] = m
            break
    for j in JOURS:
        if j in p:
            params["jour"] = j
            break
    mnb = re.search(r"\b(\d{1,3})\b", p)
    if mnb:
        params["nombre"] = int(mnb.group(1))
    return {
        "intent": best["intent"],
        "route": best["route"],
        "methode": best["methode"],
        "exemple": best["exemple"],
        "params_attendus": best["params_hint"],
        "params_detectes": params,
        "confiance": min(100, best_score * 40),
    }


def register(app):
    try:
        from prof_routes import require_token as _rt
    except Exception:  # pragma: no cover

        def _rt(f):
            return f

    @_rt
    def router():
        d = request.get_json(force=True, silent=True) or {}
        phrase = str(d.get("phrase", ""))[:200]
        if not phrase.strip():
            return jsonify({"error": "phrase vide"}), 400
        res = _detect(phrase)
        if not res:
            return jsonify({"trouve": False, "phrase": phrase})
        # incrémente les hits (apprentissage d'usage, 0 token)
        try:
            c = _conn()
            c.execute(
                "UPDATE kb_keywords SET hits=hits+1 WHERE intent=?", (res["intent"],)
            )
            c.commit()
            c.close()
        except Exception:
            pass
        return jsonify({"trouve": True, "phrase": phrase, **res})

    @_rt
    def router_lib():
        rows = _conn().execute(
            "SELECT intent, route, mots_cles, exemple, hits FROM kb_keywords ORDER BY hits DESC"
        )
        return jsonify([dict(r) for r in rows])

    app.add_url_rule("/api/router", "barre_router", router, methods=["POST"])
    app.add_url_rule("/api/router/lib", "barre_router_lib", router_lib, methods=["GET"])
    print("[Pousseline] Barre magique chargée (/api/router)")
