# -*- coding: utf-8 -*-
"""Module Histoire de la semaine — fil rouge narratif (0 token, déporté).

Génère un récit hebdomadaire avec un personnage récurrent qui RELIE les notions
de la semaine (tirées de la banque via les domaines 2026). Variantes d'ambiance
selon l'humeur de la classe (calme / dynamique) pour apaiser ou canaliser.
Contenu générique (sans PII) → cache=True. Branché par server.py via register(app).
"""

import json
import sqlite3
from pathlib import Path

from flask import jsonify, request

import ai_local

ECOLE_DB = str(Path(__file__).resolve().parent / "ecole.db")


def _conn():
    c = sqlite3.connect(ECOLE_DB)
    c.row_factory = sqlite3.Row
    return c


def _init():
    c = _conn()
    c.execute(
        """CREATE TABLE IF NOT EXISTS histoires(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        niveau TEXT, semaine INTEGER, theme TEXT, humeur TEXT,
        recit_md TEXT, exercices_lies_json TEXT, backend TEXT,
        created_at TEXT DEFAULT (datetime('now')), UNIQUE(niveau,semaine))"""
    )
    c.commit()
    c.close()


def _notions_semaine(niveau, semaine):
    """Notions à relier cette semaine : une par domaine, en rotation par semaine."""
    try:
        import banque_annuelle as b

        domaines = b.DOMAINES_2026
        dom_of = b.domaine_2026
    except Exception:
        domaines, dom_of = [], lambda m: m
    rows = (
        _conn()
        .execute("SELECT matiere, notion FROM banque WHERE niveau=?", (niveau,))
        .fetchall()
    )
    par_dom = {}
    for r in rows:
        par_dom.setdefault(dom_of(r["matiere"]), []).append(r["notion"])
    out = []
    idx = max(0, int(semaine) - 1)
    for d in domaines or list(par_dom.keys()):
        lst = par_dom.get(d, [])
        if lst:
            out.append({"domaine": d, "notion": lst[idx % len(lst)]})
    return out


def register(app):
    _init()
    try:
        from prof_routes import require_token as _rt
    except Exception:  # pragma: no cover

        def _rt(f):
            return f

    @_rt
    def histoire_generer():
        d = request.get_json(force=True, silent=True) or {}
        niveau = str(d.get("niveau", "MS"))[:8]
        semaine = int(d.get("semaine", 1) or 1)
        theme = str(d.get("theme", ""))[:80]
        humeur = str(d.get("humeur", "calme"))[:20]  # calme | dynamique | fatiguée
        notions = _notions_semaine(niveau, semaine)
        liste = "; ".join(
            f"{n['notion']} ({n['domaine'].split(' ')[0]})" for n in notions
        )
        ambiance = {
            "calme": "récit doux, apaisant, rythme lent, pour canaliser une classe agitée",
            "dynamique": "récit vivant, participatif, avec des actions à mimer",
            "fatiguée": "récit court et rassurant, voix posée, pour une classe fatiguée",
        }.get(humeur, "récit adapté à de jeunes enfants")
        prompt = (
            f"Écris une « histoire de la semaine » (fil rouge narratif) pour une classe de {niveau} "
            f"(maternelle, école française), semaine {semaine}"
            + (f", thème « {theme} »" if theme else "")
            + ".\n"
            f"Un personnage récurrent vit une aventure qui fait TRAVAILLER NATURELLEMENT ces notions : {liste}.\n"
            f"Ambiance : {ambiance}.\n"
            "Structure : titre, le récit (5-8 courts paragraphes), puis « Pistes en classe » : "
            "pour chaque notion, une activité reliée à l'histoire. Français simple, prêt à lire à voix haute. Markdown."
        )
        try:
            res = ai_local.generate(prompt, max_tokens=1600, cache=True)
        except ai_local.AIUnavailable as e:
            return jsonify({"error": str(e)}), 503
        try:
            c = _conn()
            c.execute(
                "INSERT INTO histoires(niveau,semaine,theme,humeur,recit_md,exercices_lies_json,backend) "
                "VALUES(?,?,?,?,?,?,?) ON CONFLICT(niveau,semaine) DO UPDATE SET "
                "theme=excluded.theme, humeur=excluded.humeur, recit_md=excluded.recit_md, "
                "exercices_lies_json=excluded.exercices_lies_json, backend=excluded.backend",
                (
                    niveau,
                    semaine,
                    theme,
                    humeur,
                    res["text"],
                    json.dumps(notions, ensure_ascii=False),
                    res["backend"],
                ),
            )
            c.commit()
            c.close()
        except Exception:
            pass
        return jsonify(
            {
                "niveau": niveau,
                "semaine": semaine,
                "notions": notions,
                "recit_md": res["text"],
                "backend": res["backend"],
                "cached": res["cached"],
            }
        )

    @_rt
    def histoire_liste():
        niveau = request.args.get("niveau")
        q = "SELECT id,niveau,semaine,theme,humeur,backend,created_at FROM histoires"
        a = []
        if niveau:
            q += " WHERE niveau=?"
            a.append(niveau)
        q += " ORDER BY niveau, semaine"
        return jsonify([dict(r) for r in _conn().execute(q, a)])

    @_rt
    def histoire_une():
        r = (
            _conn()
            .execute("SELECT * FROM histoires WHERE id=?", (request.args.get("id"),))
            .fetchone()
        )
        if not r:
            return jsonify({"error": "introuvable"}), 404
        return jsonify(dict(r))

    app.add_url_rule(
        "/api/histoire/generer", "histoire_generer", histoire_generer, methods=["POST"]
    )
    app.add_url_rule("/api/histoire", "histoire_liste", histoire_liste, methods=["GET"])
    app.add_url_rule("/api/histoire/une", "histoire_une", histoire_une, methods=["GET"])
    print("[Pousseline] Histoire de la semaine chargée (/api/histoire/*)")
