#!/usr/bin/env python3
"""
requestly.py — lecture des collections Requestly locales (projets « local-first »).

Requestly stocke ses Local Projects en fichiers sur le disque de l'utilisateur.
Chaque requête est un dossier contenant `__metadata.json`, et — PIÈGE — l'URL est
à la RACINE de ce fichier (`{"type":"api","url":...,"method":...}`), PAS sous une
clé `request`. Chercher `d["request"]["url"]` renvoie zéro résultat sur un projet
de 2 300 fichiers et fait conclure à tort que les collections sont vides.

API : collections() -> dict[str, list[dict]] · trouver(collection, nom) -> dict
Stdlib-only.
"""

import json
import os
from pathlib import Path

BASE = Path(
    os.environ.get(
        "JARVIS_REQUESTLY_ROOT",
        Path.home() / "Documents" / "api request" / "api",
    )
)


def _lire(path):
    try:
        d = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


def collections(base=None):
    """Retourne {nom_collection: [{name, path, method, url}, ...]}."""
    racine = Path(base) if base else BASE
    out = {}
    if not racine.is_dir():
        return out
    for meta in racine.rglob("__metadata.json"):
        d = _lire(meta)
        if not d or d.get("type") != "api" or not d.get("url"):
            continue
        rel = meta.parent.relative_to(racine)
        parties = rel.parts
        # l'arbo réelle est <racine>/apis/<collection>/<requete>/__metadata.json :
        # sans ce décalage, TOUT retombe dans une pseudo-collection nommée "apis".
        if parties and parties[0] == "apis":
            parties = parties[1:]
        collection = parties[0] if parties else "(racine)"
        nom = parties[-1] if parties else meta.parent.name
        out.setdefault(collection, []).append(
            {
                "name": nom,
                "path": str(rel),
                "method": d.get("method", "GET"),
                "url": d["url"],
                "contentType": d.get("contentType"),
            }
        )
    for v in out.values():
        v.sort(key=lambda r: r["name"])
    return out


def trouver(collection, nom, base=None):
    """Retourne la requête {name, method, url} ou None. Nom insensible à la casse."""
    cols = collections(base)
    cible = cols.get(collection)
    if cible is None:
        for k, v in cols.items():
            if k.lower() == collection.lower():
                cible = v
                break
    if not cible:
        return None
    for r in cible:
        if r["name"].lower() == nom.lower() or r["path"].lower() == nom.lower():
            return r
    return None
