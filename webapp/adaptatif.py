#!/usr/bin/env python3
"""Module Moteur adaptatif — Pousseline s'auto-régule à partir de ce que la prof
alimente dans la semaine.

Principe (on-demand, jamais en boucle → 0 risque thermique) :
1. La prof dépose des "commandes/observations" tout au long de la semaine
   (besoin d'un élève, actualité, sortie, problème rencontré) → table journal_semaine.
2. Sur demande (bouton « Actualiser la semaine »), le moteur lit le journal +
   les élèves/besoins + l'emploi du temps, et génère via la cascade IA locale
   (0 token) des propositions ADAPTÉES : exercices par élève/groupe, ajustements
   d'EDT, contenu à préparer.

Routes :
- POST   /api/adaptatif/note        {categorie, texte}  → ajoute une observation
- GET    /api/adaptatif/journal                          → liste les observations
- DELETE /api/adaptatif/note/<id>                         → supprime une observation
- POST   /api/adaptatif/actualiser                        → génère les adaptations
"""

import sqlite3
from pathlib import Path
from flask import jsonify, request

DB = Path(__file__).resolve().parent / "ecole.db"
CATS = ("eleve", "actualite", "sortie", "probleme", "demande", "recherche", "note")


def _conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def _init():
    with _conn() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS journal_semaine (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT DEFAULT (datetime('now','localtime')),
                categorie TEXT DEFAULT 'note',
                texte TEXT NOT NULL,
                traite INTEGER DEFAULT 0
            )"""
        )
        c.commit()


def _contexte():
    """Rassemble le contexte réel (élèves, EDT) pour ancrer la génération."""
    ctx = {"eleves": [], "edt": [], "journal": []}
    with _conn() as c:
        try:
            for r in c.execute("SELECT nom, prenom FROM eleves LIMIT 30"):
                ctx["eleves"].append(f"{r['prenom']} {r['nom']}".strip())
        except sqlite3.Error:
            pass
        try:
            for r in c.execute(
                "SELECT jour,debut,fin,matiere FROM edt_creneaux ORDER BY jour,debut LIMIT 40"
            ):
                ctx["edt"].append(
                    f"j{r['jour']} {r['debut']}-{r['fin']} {r['matiere']}"
                )
        except sqlite3.Error:
            pass
        for r in c.execute(
            "SELECT id,categorie,texte FROM journal_semaine WHERE traite=0 ORDER BY ts DESC LIMIT 40"
        ):
            ctx["journal"].append(
                {"id": r["id"], "cat": r["categorie"], "txt": r["texte"]}
            )
    return ctx


def register(app):
    _init()
    try:
        from prof_routes import require_token
    except Exception:

        def require_token(f):
            return f

    @app.route("/api/adaptatif/note", methods=["POST"])
    @require_token
    def adapt_note():
        d = request.get_json(force=True, silent=True) or {}
        texte = str(d.get("texte", "")).strip()[:500]
        cat = str(d.get("categorie", "note")).strip().lower()
        if cat not in CATS:
            cat = "note"
        if not texte:
            return jsonify({"ok": False, "error": "texte requis"}), 400
        with _conn() as c:
            cur = c.execute(
                "INSERT INTO journal_semaine(categorie,texte) VALUES(?,?)", (cat, texte)
            )
            c.commit()
        return jsonify({"ok": True, "id": cur.lastrowid})

    @app.route("/api/adaptatif/journal", methods=["GET"])
    @require_token
    def adapt_journal():
        with _conn() as c:
            rows = [
                dict(r)
                for r in c.execute(
                    "SELECT * FROM journal_semaine ORDER BY ts DESC LIMIT 60"
                )
            ]
        return jsonify({"ok": True, "journal": rows})

    @app.route("/api/adaptatif/note/<int:nid>", methods=["DELETE"])
    @require_token
    def adapt_del(nid):
        with _conn() as c:
            c.execute("DELETE FROM journal_semaine WHERE id=?", (nid,))
            c.commit()
        return jsonify({"ok": True})

    @app.route("/api/adaptatif/actualiser", methods=["POST"])
    @require_token
    def adapt_actualiser():
        ctx = _contexte()
        if not ctx["journal"]:
            return jsonify(
                {"ok": False, "error": "journal vide — ajoute des observations d'abord"}
            ), 400
        obs = "\n".join(f"- [{j['cat']}] {j['txt']}" for j in ctx["journal"])
        eleves = ", ".join(ctx["eleves"][:25]) or "(non renseignés)"
        edt = "; ".join(ctx["edt"][:20]) or "(EDT vide)"
        prompt = (
            "Tu assistes une professeure des écoles. À partir de ses observations de la "
            f"semaine :\n{obs}\n\nÉlèves : {eleves}\nEmploi du temps : {edt}\n\n"
            "Propose de façon CONCISE et actionnable, en français :\n"
            "1) EXERCICES adaptés (par élève ou groupe selon les besoins observés)\n"
            "2) AJUSTEMENTS d'emploi du temps (si l'actualité/sorties/problèmes le justifient)\n"
            "3) CONTENU à préparer cette semaine.\n"
            "Réponds en listes courtes, priorités d'abord."
        )
        try:
            import ai_local

            # liste des élèves + observations de l'enseignante → ne sort pas du foyer
            r = ai_local.generate(
                prompt, max_tokens=700, cache=False, nominatif=True
            )
        except Exception as e:
            return jsonify({"ok": False, "error": f"IA indisponible : {e}"}), 503
        return jsonify(
            {
                "ok": True,
                "propositions": r["text"],
                "backend": r["backend"],
                "base": {
                    "observations": len(ctx["journal"]),
                    "eleves": len(ctx["eleves"]),
                    "creneaux": len(ctx["edt"]),
                },
            }
        )

    print("[adaptatif] module chargé (/api/adaptatif/*)")
