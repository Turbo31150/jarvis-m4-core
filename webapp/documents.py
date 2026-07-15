#!/usr/bin/env python3
"""Module Documents — rapports & banque PDF consultables dans Pousseline.

Expose les PDF pédagogiques générés par l'app (audit, banque MS/GS, etc.) :
- /api/rapports          : liste JSON des PDF disponibles (titre, taille, url)
- /rapports-pdf/<name>   : sert un PDF pour consultation/téléchargement en ligne

Réversible : retirer "documents" de la boucle d'import dans server.py suffit.
Aucune donnée élève : ces PDF sont des supports génériques (RGPD ok).
"""

from pathlib import Path
from flask import jsonify, send_file, abort

# Répertoires scannés (ordre = priorité d'affichage)
RAP_DIRS = [
    Path("/home/pamerys/jarvis/webapp/static/rapports"),
    Path("/home/pamerys/Documents"),
]
# Motifs de fichiers pédagogiques à exposer (évite d'exposer tout ~/Documents)
PATTERNS = ("audit_", "Banque_", "Cahier-journal", "rapport_", "Rapport_")


def _titre(nom: str) -> str:
    base = nom.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
    return base[:1].upper() + base[1:]


def _lister():
    vus, out = set(), []
    for d in RAP_DIRS:
        if not d.exists():
            continue
        for p in sorted(d.glob("*.pdf")):
            if p.name in vus:
                continue
            if not p.name.lower().startswith(tuple(x.lower() for x in PATTERNS)):
                continue
            vus.add(p.name)
            try:
                ko = max(1, p.stat().st_size // 1024)
            except OSError:
                ko = 0
            out.append(
                {
                    "nom": p.name,
                    "titre": _titre(p.name),
                    "taille": f"{ko} Ko" if ko < 1024 else f"{ko // 1024} Mo",
                    "url": f"/rapports-pdf/{p.name}",
                }
            )
    return out


def _resoudre(name: str):
    """Retrouve un PDF par nom dans les répertoires autorisés (anti-traversal)."""
    safe = Path(name).name  # neutralise ../
    for d in RAP_DIRS:
        cible = d / safe
        if cible.exists() and cible.suffix.lower() == ".pdf":
            return cible
    return None


# Catalogue validé de ressources pédagogiques LÉGALEMENT gratuites / libres de droits.
# Aucun manuel sous copyright. Vérifié : licence explicite ou service officiel EN.
RESSOURCES_LIBRES = [
    {
        "nom": "⭐ Programme maternelle 2026 (BO n°19, arrêté 16/04/2026)",
        "url": "https://eduscol.education.gouv.fr/sites/default/files/document/programme-d-enseignement-du-cycle-1-80130.pdf",
        "niveaux": "PS→GS",
        "matiere": "Programme officiel cycle 1 — 6 domaines",
        "licence": "Officiel EN — en vigueur rentrée 2026-2027",
    },
    {
        "nom": "⭐ Eduscol — Enseigner au cycle 1 (ressources d'accompagnement)",
        "url": "https://eduscol.education.gouv.fr/4341/enseigner-au-cycle-1",
        "niveaux": "MS/GS",
        "matiere": "Séquences & mises en œuvre",
        "licence": "Officiel Éducation nationale",
    },
    {
        "nom": "education.gouv — École maternelle",
        "url": "https://www.education.gouv.fr/programmes-et-horaires-l-ecole-maternelle-4193",
        "niveaux": "PS→GS",
        "matiere": "Programmes & horaires",
        "licence": "Officiel Éducation nationale",
    },
    {
        "nom": "Sésamath — manuels & cahiers",
        "url": "https://manuel.sesamath.net/",
        "niveaux": "primaire→collège",
        "matiere": "Mathématiques",
        "licence": "CC-BY-SA / GNU-FDL (libre, modifiable)",
    },
    {
        "nom": "Calcul@TICE — exercices en ligne",
        "url": "https://calculatice.ac-lille.fr/",
        "niveaux": "CP→CM2",
        "matiere": "Calcul / numération",
        "licence": "Gratuit (Éducation nationale, ac-Lille)",
    },
    {
        "nom": "Eduscol — j'enseigne en maternelle",
        "url": "https://eduscol.education.fr/89/j-enseigne-en-maternelle",
        "niveaux": "PS→GS",
        "matiere": "Tous domaines cycle 1",
        "licence": "Officiel Éducation nationale (réutilisable)",
    },
    {
        "nom": "Réseau Canopé",
        "url": "https://www.reseau-canope.fr/",
        "niveaux": "maternelle→lycée",
        "matiere": "Transversal",
        "licence": "Officiel Éducation nationale",
    },
    {
        "nom": "BDRP — banque de ressources pédagogiques",
        "url": "https://www.bdrp.fr/",
        "niveaux": "maternelle→primaire",
        "matiere": "Tous domaines",
        "licence": "Partage entre enseignants (gratuit)",
    },
    {
        "nom": "Manuels anciens (domaine public)",
        "url": "https://manuelsanciens.blogspot.com/",
        "niveaux": "primaire",
        "matiere": "Français / calcul",
        "licence": "Domaine public",
    },
]


def register(app):
    try:
        from prof_routes import require_token
    except Exception:

        def require_token(f):
            return f

    @app.route("/api/rapports")
    @require_token
    def api_rapports():
        return jsonify(_lister())

    @app.route("/api/ressources-libres")
    @require_token
    def api_ressources_libres():
        return jsonify(RESSOURCES_LIBRES)

    @app.route("/rapports-pdf/<path:name>")
    @require_token
    def rapports_pdf(name):
        p = _resoudre(name)
        if not p:
            abort(404)
        return send_file(str(p), mimetype="application/pdf")
