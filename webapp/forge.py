#!/usr/bin/env python3
"""Module Forge — lire et contrôler les formations produites par la cascade.

Les formations sont forgées hors ligne par scripts/forge_formations.py, qui écrit
un markdown par produit. Ce module les rend lisibles depuis la PWA et signale les
affirmations chiffrées à vérifier avant publication.

Le détecteur de chiffres est **purement déterministe** (regex, 0 inférence) : le
modèle a tendance à inventer des benchmarks crédibles (« perplexité ≤ 12 sur
WikiText-2 », « latence < 200 ms »), et sur des produits payants ce sont des
promesses fausses. Aucune IA n'est appelée pour les repérer — c'est un travail
de motif, pas de jugement.

register(app) branche /api/forge*. Réversible : retirer l'import de server.py.
"""

import json
import re
from pathlib import Path

from flask import jsonify, request

BASE = Path("/home/pamerys/jarvis")
FORGE_DIR = BASE / "data" / "forge"
INVENTAIRE = BASE / "data" / "gumroad_inventaire.json"

# Motifs d'affirmations chiffrées invérifiables. Volontairement large : mieux
# vaut un faux positif relu qu'une promesse fausse publiée.
MOTIFS = [
    (r"\b\d+(?:[.,]\d+)?\s*%", "pourcentage"),
    (r"[<>≤≥]\s*\d+(?:[.,]\d+)?\s*(?:ms|s|min|h)\b", "seuil de latence"),
    (r"\b\d+(?:[.,]\d+)?\s*(?:ms|Go|Mo|GB|MB|tok/s|tokens/s)\b", "mesure"),
    (r"\bperplexit[ée]\s*[<>≤≥=]?\s*\d+", "perplexité"),
    (r"\b(?:x|×)\s?\d+(?:[.,]\d+)?\s*(?:plus|fois)", "facteur"),
]


def _inventaire():
    if not INVENTAIRE.exists():
        return {}
    try:
        return {p["slug"]: p for p in json.loads(INVENTAIRE.read_text("utf-8"))}
    except (json.JSONDecodeError, KeyError):
        return {}


def _claims(texte):
    """Renvoie les affirmations chiffrées, avec leur ligne, sans dédoublonner
    les types : une même ligne peut porter deux promesses distinctes."""
    trouves = []
    for num, ligne in enumerate(texte.splitlines(), 1):
        for motif, genre in MOTIFS:
            for m in re.finditer(motif, ligne, re.IGNORECASE):
                trouves.append(
                    {
                        "ligne": num,
                        "genre": genre,
                        "extrait": ligne.strip()[:200],
                        "valeur": m.group(0),
                    }
                )
    return trouves


def register(app):
    @app.route("/api/forge")
    def forge_liste():
        inv = _inventaire()
        items = []
        for f in sorted(FORGE_DIR.glob("*.md")) if FORGE_DIR.exists() else []:
            texte = f.read_text("utf-8", errors="replace")
            prod = inv.get(f.stem, {})
            items.append(
                {
                    "slug": f.stem,
                    "titre": prod.get("titre") or f.stem.replace("-", " ").title(),
                    "prix": prod.get("prix") or "",
                    "mots": len(texte.split()),
                    "modules": texte.count("## Module"),
                    "a_verifier": len(_claims(texte)),
                }
            )
        return jsonify(
            {
                "forgees": len(items),
                "inventaire": len(inv),
                "restantes": max(0, len(inv) - len(items)),
                "formations": items,
            }
        )

    @app.route("/api/forge/<slug>")
    def forge_lire(slug):
        # Le slug vient de l'URL : on le contraint avant de toucher au disque.
        if not re.fullmatch(r"[a-z0-9-]{1,80}", slug):
            return jsonify({"error": "slug invalide"}), 400
        f = FORGE_DIR / f"{slug}.md"
        if not f.exists():
            return jsonify({"error": "formation non forgée"}), 404
        texte = f.read_text("utf-8", errors="replace")
        prod = _inventaire().get(slug, {})
        return jsonify(
            {
                "slug": slug,
                "titre": prod.get("titre") or slug,
                "prix": prod.get("prix") or "",
                "markdown": texte,
                "a_verifier": _claims(texte) if request.args.get("claims") else None,
            }
        )

    @app.route("/api/forge/claims")
    def forge_claims():
        """Toutes les affirmations chiffrées du corpus, les plus chargées d'abord.
        Sert de file de relecture avant publication."""
        out = []
        for f in sorted(FORGE_DIR.glob("*.md")) if FORGE_DIR.exists() else []:
            c = _claims(f.read_text("utf-8", errors="replace"))
            if c:
                out.append({"slug": f.stem, "nb": len(c), "claims": c[:40]})
        out.sort(key=lambda x: -x["nb"])
        return jsonify(
            {"fichiers": len(out), "total": sum(x["nb"] for x in out), "detail": out}
        )
