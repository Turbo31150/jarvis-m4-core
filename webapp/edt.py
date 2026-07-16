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
            # Détection de conflit : 2 créneaux le même jour se chevauchent si
            # debut < fin_existant ET debut_existant < fin. On refuse (fail-closed).
            nd, nf = _minutes(debut), _minutes(fin)
            for r in c.execute(
                "SELECT debut, fin, matiere FROM edt_creneaux WHERE jour=?", (jour,)
            ).fetchall():
                if nd < _minutes(r["fin"]) and _minutes(r["debut"]) < nf:
                    return jsonify(
                        {
                            "error": "conflit de créneau",
                            "conflit": f"{r['matiere']} {r['debut']}–{r['fin']}",
                        }
                    ), 409
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

    @app.route("/api/edt/generer", methods=["POST"])
    def edt_generer():
        """Propose un emploi du temps hebdo complet via IA (respect ~24h + volumes officiels).
        Ne touche PAS la base : renvoie une proposition à valider puis appliquer."""
        import json as _json

        import ai_local

        d = request.get_json(force=True, silent=True) or {}
        niveau = str(d.get("niveau", "CE2")).strip()[:30]
        contraintes = str(d.get("contraintes", "")).strip()[:500]
        prompt = (
            f"Tu es enseignante en primaire (France). Construis un emploi du temps "
            f"hebdomadaire COMPLET pour une classe de {niveau}, du lundi au vendredi, "
            f"environ 24h d'enseignement, en respectant les volumes officiels du B.O. "
            f"(français ~10h, maths ~5h en cycle 2 ; EPS, langue vivante, "
            f"questionner le monde/sciences, arts, EMC, récréations). "
            f"Journée type 8h30-11h30 et 13h30-16h30, récréations 10h15-10h30 et 15h-15h15. "
            f"{('Contraintes : ' + contraintes) if contraintes else ''}\n"
            "Réponds UNIQUEMENT par un tableau JSON, sans texte autour, de la forme : "
            '[{"jour":0,"debut":"08:30","fin":"09:30","matiere":"Français","domaine":"français"}], '
            "jour: 0=lundi..4=vendredi. Pas de créneau le mercredi après-midi."
        )
        try:
            res = ai_local.generate(
                prompt, max_tokens=2000, cache=True, temperature=0.4
            )
        except ai_local.AIUnavailable as e:
            return jsonify({"error": str(e)}), 503
        txt = res["text"]
        # extraire le tableau JSON même si l'IA ajoute du texte
        creneaux = []
        try:
            s, e = txt.find("["), txt.rfind("]")
            if s >= 0 and e > s:
                creneaux = _json.loads(txt[s : e + 1])
        except Exception:
            creneaux = []
        # nettoyer/valider chaque créneau
        clean = []
        for c in creneaux if isinstance(creneaux, list) else []:
            if not isinstance(c, dict):
                continue
            deb, fin = str(c.get("debut", ""))[:5], str(c.get("fin", ""))[:5]
            mat = str(c.get("matiere", "")).strip()[:60]
            if mat and _duree(deb, fin) > 0:
                clean.append(
                    {
                        "jour": _clamp(c.get("jour"), 0, 0, 5),
                        "debut": deb,
                        "fin": fin,
                        "matiere": mat,
                        "domaine": str(c.get("domaine", "")).strip()[:60],
                        "niveau": niveau,
                    }
                )
        if not clean:
            return jsonify(
                {
                    "error": "L'IA n'a pas renvoyé d'emploi du temps exploitable. Réessaie.",
                    "brut": txt[:400],
                }
            ), 502
        return jsonify(
            {"ok": True, "creneaux": clean, "backend": res["backend"], "nb": len(clean)}
        )

    @app.route("/api/edt/appliquer", methods=["POST"])
    def edt_appliquer():
        """Insère une proposition validée. remplacer=True vide d'abord l'EDT existant."""
        d = request.get_json(force=True, silent=True) or {}
        creneaux = d.get("creneaux") or []
        if not isinstance(creneaux, list) or not creneaux:
            return jsonify({"error": "Aucun créneau à appliquer"}), 400
        with _conn() as c:
            if d.get("remplacer"):
                c.execute("DELETE FROM edt_creneaux")
            n = 0
            for cr in creneaux:
                if not isinstance(cr, dict):
                    continue
                deb, fin = str(cr.get("debut", ""))[:5], str(cr.get("fin", ""))[:5]
                mat = str(cr.get("matiere", "")).strip()[:60]
                if not mat or _duree(deb, fin) <= 0:
                    continue
                c.execute(
                    "INSERT INTO edt_creneaux(jour,debut,fin,matiere,domaine,niveau) "
                    "VALUES(?,?,?,?,?,?)",
                    (
                        _clamp(cr.get("jour"), 0, 0, 5),
                        deb,
                        fin,
                        mat,
                        str(cr.get("domaine", "")).strip()[:60],
                        str(cr.get("niveau", "")).strip()[:30],
                    ),
                )
                n += 1
            c.commit()
        return jsonify({"ok": True, "inseres": n})

    print(
        "[Pousseline] Emploi du temps chargé (/api/edt/creneaux, /api/edt/volumes, /api/edt/generer)"
    )
