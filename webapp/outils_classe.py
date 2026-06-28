#!/usr/bin/env python3
"""Outils Classe — module autonome de l'Espace Prof.

Quatre outils du quotidien :
  • Générateur de problèmes de maths (IA locale 0-token)
  • Rituels du matin : dictée flash / phrase du jour / calcul mental / jogging
    d'écriture (IA locale 0-token)
  • Suivi comportement : points +/- par élève (base ecole.db)
  • Ceintures de compétences : couleur par domaine et par élève (base ecole.db)

Le tirage au sort et le minuteur sont 100 % front (index.html), hors-ligne.

Branché par server.py via register(app). Réutilise les helpers de prof_routes
(require_token, _body, _rows, _write, _clamp) pour rester cohérent et protégé.
"""

import ai_local
import prof_routes as _pr

# Helpers partagés avec l'Espace Prof (même token, même base)
require_token = _pr.require_token
_body = _pr._body
_rows = _pr._rows
_write = _pr._write
_clamp = _pr._clamp

from flask import jsonify  # noqa: E402

CEINTURES = ["blanche", "jaune", "orange", "verte", "bleue", "marron", "noire"]


def register(app):
    # ── PROBLÈMES DE MATHS ───────────────────────────────────────────────
    @app.route("/api/prof/probleme-maths", methods=["POST"])
    @require_token
    def probleme_maths():
        d = _body()
        niveau = str(d.get("niveau", "CE2"))[:8]
        typ = str(d.get("type", "additif"))[:40]
        theme = str(d.get("theme", ""))[:120]
        nb = _clamp(d.get("nb", 4), 4, 1, 12)
        ctx = f" Contextualise sur le thème « {theme} »." if theme else ""
        prompt = (
            f"Crée {nb} problèmes de mathématiques de type {typ} pour des élèves de "
            f"{niveau} (école primaire France).{ctx}\n"
            "Énoncés courts, nombres adaptés au niveau, une question claire par "
            "problème. Donne ENSUITE le corrigé détaillé (opération posée + phrase "
            "réponse) sous un titre ## Corrigé. Markdown, prêt à imprimer."
        )
        try:
            res = ai_local.generate(prompt, max_tokens=1100, cache=True)
        except ai_local.AIUnavailable as e:
            return jsonify({"error": str(e)}), 503
        return jsonify(
            {
                "contenu_md": res["text"],
                "backend": res["backend"],
                "cached": res["cached"],
            }
        )

    # ── RITUELS DU MATIN ─────────────────────────────────────────────────
    @app.route("/api/prof/rituel", methods=["POST"])
    @require_token
    def rituel():
        d = _body()
        niveau = str(d.get("niveau", "CE2"))[:8]
        genre = str(d.get("genre", "phrase_du_jour"))[:30]
        notion = str(d.get("notion", ""))[:120]
        consignes = {
            "dictee_flash": "Propose une dictée flash : 5 phrases courtes du jour, "
            "progressives, avec les difficultés orthographiques soulignées et un "
            "rappel de la règle visée.",
            "phrase_du_jour": "Propose une phrase du jour à analyser : 1 phrase + "
            "3 questions (nature/fonction des mots, conjugaison, orthographe).",
            "calcul_mental": "Propose une série de 10 calculs mentaux progressifs "
            "avec le corrigé, et la procédure experte à expliciter.",
            "jogging_ecriture": "Propose 3 amorces de jogging d'écriture "
            "(inducteurs) motivantes et un mot-objectif d'écriture.",
        }
        base = consignes.get(genre, consignes["phrase_du_jour"])
        ctx = f" Notion ciblée : {notion}." if notion else ""
        prompt = (
            f"Rituel du matin pour des élèves de {niveau} (primaire France). {base}"
            f"{ctx}\nMarkdown clair, prêt à projeter au tableau."
        )
        try:
            res = ai_local.generate(prompt, max_tokens=900, cache=True)
        except ai_local.AIUnavailable as e:
            return jsonify({"error": str(e)}), 503
        return jsonify(
            {
                "contenu_md": res["text"],
                "backend": res["backend"],
                "cached": res["cached"],
            }
        )

    # ── SUIVI COMPORTEMENT (points +/-) ──────────────────────────────────
    @app.route("/api/prof/comportement", methods=["GET", "POST"])
    @require_token
    def comportement():
        from flask import request

        if request.method == "POST":
            d = _body()
            eid = _clamp(d.get("eleve_id"), 0, 0, 10**9)
            if not eid:
                return jsonify({"error": "eleve_id requis"}), 400
            delta = _clamp(d.get("delta", 1), 1, -50, 50)
            motif = str(d.get("motif", ""))[:120]
            _write(
                "INSERT INTO comportement(eleve_id, delta, motif) VALUES(?,?,?)",
                (eid, delta, motif),
            )
            return jsonify({"ok": True})
        # GET : total de points par élève
        rows = _rows(
            "SELECT e.id, e.prenom, e.nom, e.niveau, "
            "COALESCE(SUM(c.delta),0) AS points "
            "FROM eleves e LEFT JOIN comportement c ON c.eleve_id=e.id "
            "GROUP BY e.id ORDER BY e.niveau, e.nom"
        )
        return jsonify(rows)

    # ── CEINTURES DE COMPÉTENCES ─────────────────────────────────────────
    @app.route("/api/prof/ceintures", methods=["GET", "POST"])
    @require_token
    def ceintures():
        from flask import request

        if request.method == "POST":
            d = _body()
            eid = _clamp(d.get("eleve_id"), 0, 0, 10**9)
            domaine = str(d.get("domaine", ""))[:60]
            couleur = str(d.get("couleur", "blanche"))[:20]
            if not eid or not domaine:
                return jsonify({"error": "eleve_id et domaine requis"}), 400
            if couleur not in CEINTURES:
                couleur = "blanche"
            # upsert : une ceinture par (élève, domaine)
            _write(
                "INSERT INTO ceintures(eleve_id, domaine, couleur) VALUES(?,?,?) "
                "ON CONFLICT(eleve_id, domaine) DO UPDATE SET couleur=excluded.couleur",
                (eid, domaine, couleur),
            )
            return jsonify({"ok": True})
        rows = _rows(
            "SELECT c.eleve_id, e.prenom, e.nom, c.domaine, c.couleur "
            "FROM ceintures c JOIN eleves e ON e.id=c.eleve_id "
            "ORDER BY e.nom, c.domaine"
        )
        return jsonify({"ceintures": rows, "couleurs": CEINTURES})

    print(
        "[JARVIS] Outils Classe chargés (problèmes, rituels, comportement, ceintures)"
    )
