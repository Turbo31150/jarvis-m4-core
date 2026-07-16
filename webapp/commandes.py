#!/usr/bin/env python3
"""Module Commandes & Budget — gérer le budget de classe et générer les listes de
commande de matériel depuis l'audit (besoins), branché sur la cascade IA locale 0-token.

Tables (ecole.db) :
- budget_classe   : montant total, réserve mise de côté, note
- commande_lignes : article, quantité, prix unit., total, section, statut (à commander/commandé)

Routes :
- GET/POST /api/commandes/budget                → lire / définir le budget + réserve
- GET      /api/commandes/lignes                → lignes de commande + totaux
- POST     /api/commandes/ligne                 → ajouter une ligne
- DELETE   /api/commandes/ligne/<id>            → supprimer
- POST     /api/commandes/generer {audit}       → génère les lignes depuis un texte d'audit (cascade IA)

Cascade : cache SQL → Ollama local → cloud (via ai_local). On-demand, jamais en boucle.
"""

import json
import sqlite3
from pathlib import Path
from flask import jsonify, request

DB = Path(__file__).resolve().parent / "ecole.db"


def _conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def _init():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS budget_classe (
            id INTEGER PRIMARY KEY CHECK (id=1),
            total REAL DEFAULT 0, reserve REAL DEFAULT 0, note TEXT DEFAULT '')""")
        c.execute("""CREATE TABLE IF NOT EXISTS commande_lignes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article TEXT NOT NULL, quantite TEXT DEFAULT '', prix REAL DEFAULT 0,
            total REAL DEFAULT 0, section TEXT DEFAULT '', statut TEXT DEFAULT 'a_commander',
            fournisseur TEXT DEFAULT '')""")
        c.execute("INSERT OR IGNORE INTO budget_classe(id,total,reserve) VALUES(1,0,0)")
        c.commit()


def _totaux(c):
    lignes = c.execute(
        "SELECT COALESCE(SUM(total),0) t FROM commande_lignes"
    ).fetchone()["t"]
    b = c.execute("SELECT total,reserve FROM budget_classe WHERE id=1").fetchone()
    dispo = (b["total"] or 0) - (b["reserve"] or 0)
    return {
        "total_commande": round(lignes, 2),
        "budget": b["total"] or 0,
        "reserve": b["reserve"] or 0,
        "disponible": round(dispo, 2),
        "reste": round(dispo - lignes, 2),
    }


def register(app):
    _init()
    try:
        from prof_routes import require_token
    except Exception:

        def require_token(f):
            return f

    @app.route("/api/commandes/budget", methods=["GET", "POST"])
    @require_token
    def cmd_budget():
        with _conn() as c:
            if request.method == "POST":
                d = request.get_json(force=True, silent=True) or {}
                c.execute(
                    "UPDATE budget_classe SET total=?,reserve=?,note=? WHERE id=1",
                    (
                        float(d.get("total", 0) or 0),
                        float(d.get("reserve", 0) or 0),
                        str(d.get("note", ""))[:200],
                    ),
                )
                c.commit()
            b = dict(c.execute("SELECT * FROM budget_classe WHERE id=1").fetchone())
            b.update(_totaux(c))
        return jsonify({"ok": True, **b})

    @app.route("/api/commandes/lignes")
    @require_token
    def cmd_lignes():
        with _conn() as c:
            lignes = [
                dict(r)
                for r in c.execute("SELECT * FROM commande_lignes ORDER BY section, id")
            ]
            tot = _totaux(c)
        return jsonify({"ok": True, "lignes": lignes, **tot})

    @app.route("/api/commandes/ligne", methods=["POST"])
    @require_token
    def cmd_add():
        d = request.get_json(force=True, silent=True) or {}
        art = str(d.get("article", "")).strip()[:120]
        if not art:
            return jsonify({"ok": False, "error": "article requis"}), 400
        q = str(d.get("quantite", ""))[:30]
        prix = float(d.get("prix", 0) or 0)
        try:
            qn = float(str(q).split()[0].replace(",", "."))
        except (ValueError, IndexError):
            qn = 1
        total = round(prix * qn, 2)
        with _conn() as c:
            cur = c.execute(
                "INSERT INTO commande_lignes(article,quantite,prix,total,section,fournisseur) "
                "VALUES(?,?,?,?,?,?)",
                (
                    art,
                    q,
                    prix,
                    total,
                    str(d.get("section", ""))[:60],
                    str(d.get("fournisseur", ""))[:80],
                ),
            )
            c.commit()
            rid = cur.lastrowid
        return jsonify({"ok": True, "id": rid, "total": total})

    @app.route("/api/commandes/ligne/<int:lid>", methods=["DELETE"])
    @require_token
    def cmd_del(lid):
        with _conn() as c:
            c.execute("DELETE FROM commande_lignes WHERE id=?", (lid,))
            c.commit()
        return jsonify({"ok": True})

    @app.route("/api/commandes/generer", methods=["POST"])
    @require_token
    def cmd_generer():
        d = request.get_json(force=True, silent=True) or {}
        audit = str(d.get("audit", "")).strip()[:2500]
        if not audit:
            return jsonify(
                {"ok": False, "error": "colle le texte d'audit/besoins"}
            ), 400
        with _conn() as c:
            b = c.execute(
                "SELECT total,reserve FROM budget_classe WHERE id=1"
            ).fetchone()
            dispo = (b["total"] or 0) - (b["reserve"] or 0)
        prompt = (
            "À partir de ces besoins de matériel scolaire :\n"
            + audit
            + f"\n\nBudget disponible : {dispo:.0f} euros. Renvoie UNIQUEMENT un tableau JSON "
            '(pas de texte autour) : [{"article":"...","quantite":"...","prix":0.0,'
            '"section":"..."}]. Prix unitaires indicatifs réalistes (catalogue scolaire FR), '
            "total ≤ budget. Priorise l'essentiel."
        )
        try:
            import ai_local

            r = ai_local.generate(prompt, max_tokens=1200, cache=True)
        except Exception as e:
            return jsonify({"ok": False, "error": f"IA indisponible : {e}"}), 503
        txt = r["text"]
        # extraire le JSON (le modèle peut l'entourer de texte)
        i, j = txt.find("["), txt.rfind("]")
        if i < 0 or j < 0:
            return jsonify(
                {"ok": False, "error": "réponse IA non exploitable", "brut": txt[:400]}
            ), 502
        try:
            items = json.loads(txt[i : j + 1])
        except json.JSONDecodeError:
            return jsonify(
                {"ok": False, "error": "JSON invalide", "brut": txt[i : j + 1][:400]}
            ), 502
        n = 0
        with _conn() as c:
            for it in items[:60]:
                art = str(it.get("article", "")).strip()[:120]
                if not art:
                    continue
                q = str(it.get("quantite", ""))[:30]
                prix = float(it.get("prix", 0) or 0)
                try:
                    qn = float(str(q).split()[0].replace(",", "."))
                except (ValueError, IndexError):
                    qn = 1
                c.execute(
                    "INSERT INTO commande_lignes(article,quantite,prix,total,section) "
                    "VALUES(?,?,?,?,?)",
                    (
                        art,
                        q,
                        prix,
                        round(prix * qn, 2),
                        str(it.get("section", ""))[:60],
                    ),
                )
                n += 1
            c.commit()
            tot = _totaux(c)
        return jsonify({"ok": True, "ajoutees": n, "backend": r["backend"], **tot})

    print("[commandes] module chargé (/api/commandes/*)")
