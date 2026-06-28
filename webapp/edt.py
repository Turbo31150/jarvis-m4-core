"""Module Emploi du temps structuré (Pousseline / Espace Prof).
Créneaux en base (pas un blob JSON) → calcul automatique des volumes horaires par
matière et par domaine, pour vérifier le respect des horaires officiels.
SQL pur : aucune inférence IA, aucune chauffe. Protégé par le garde global /api/.
"""

import sqlite3
from pathlib import Path

from flask import jsonify, request

ECOLE_DB = str(Path(__file__).resolve().parent / "ecole.db")
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"]


def _conn():
    c = sqlite3.connect(ECOLE_DB)
    c.row_factory = sqlite3.Row
    return c


def _init():
    with _conn() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS edt_creneaux (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                jour    INTEGER NOT NULL,          -- 0=lundi … 5=samedi
                debut   TEXT NOT NULL,             -- 'HH:MM'
                fin     TEXT NOT NULL,             -- 'HH:MM'
                matiere TEXT NOT NULL,
                domaine TEXT DEFAULT '',           -- domaine programme (français, maths…)
                niveau  TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )"""
        )
        c.commit()


def _minutes(hhmm):
    """'HH:MM' → minutes depuis minuit. Renvoie 0 si invalide."""
    try:
        h, m = hhmm.split(":")
        return max(0, min(24 * 60, int(h) * 60 + int(m)))
    except Exception:
        return 0


def _duree(deb, fin):
    d = _minutes(fin) - _minutes(deb)
    return d if d > 0 else 0


def _clamp(v, defaut, lo, hi):
    try:
        return max(lo, min(hi, int(v)))
    except Exception:
        return defaut


def register(app):
    _init()

    @app.route("/api/edt/creneaux", methods=["GET"])
    def edt_list():
        with _conn() as c:
            rows = c.execute(
                "SELECT * FROM edt_creneaux ORDER BY jour, debut"
            ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["jour_nom"] = JOURS[d["jour"]] if 0 <= d["jour"] < len(JOURS) else "?"
            d["duree_min"] = _duree(d["debut"], d["fin"])
            out.append(d)
        return jsonify(out)

    @app.route("/api/edt/creneaux", methods=["POST"])
    def edt_add():
        d = request.get_json(force=True, silent=True) or {}
        jour = _clamp(d.get("jour"), 0, 0, 5)
        debut = str(d.get("debut", ""))[:5]
        fin = str(d.get("fin", ""))[:5]
        matiere = str(d.get("matiere", "")).strip()[:60]
        domaine = str(d.get("domaine", "")).strip()[:60]
        niveau = str(d.get("niveau", "")).strip()[:30]
        if not matiere or _duree(debut, fin) <= 0:
            return jsonify({"error": "matiere requise et fin > debut"}), 400
        with _conn() as c:
            cur = c.execute(
                "INSERT INTO edt_creneaux(jour,debut,fin,matiere,domaine,niveau) "
                "VALUES(?,?,?,?,?,?)",
                (jour, debut, fin, matiere, domaine, niveau),
            )
            c.commit()
            rid = cur.lastrowid
        return jsonify({"ok": True, "id": rid})

    @app.route("/api/edt/creneaux/<int:cid>", methods=["DELETE"])
    def edt_del(cid):
        with _conn() as c:
            c.execute("DELETE FROM edt_creneaux WHERE id=?", (cid,))
            c.commit()
        return jsonify({"ok": True})

    @app.route("/api/edt/volumes", methods=["GET"])
    def edt_volumes():
        """Totaux horaires hebdo par matière et par domaine (minutes → h:min)."""
        with _conn() as c:
            rows = c.execute("SELECT * FROM edt_creneaux").fetchall()
        par_matiere, par_domaine, total = {}, {}, 0
        for r in rows:
            dur = _duree(r["debut"], r["fin"])
            total += dur
            par_matiere[r["matiere"]] = par_matiere.get(r["matiere"], 0) + dur
            dom = r["domaine"] or "(non classé)"
            par_domaine[dom] = par_domaine.get(dom, 0) + dur

        def fmt(m):
            return f"{m // 60}h{m % 60:02d}"

        return jsonify(
            {
                "total_min": total,
                "total_h": fmt(total),
                "par_matiere": {
                    k: {"min": v, "h": fmt(v)} for k, v in par_matiere.items()
                },
                "par_domaine": {
                    k: {"min": v, "h": fmt(v)} for k, v in par_domaine.items()
                },
            }
        )

    print("[Pousseline] Emploi du temps chargé (/api/edt/creneaux, /api/edt/volumes)")
