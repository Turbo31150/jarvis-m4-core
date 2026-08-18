#!/usr/bin/env python3
"""
env.py — loader .env canonique de l'écosystème JARVIS (étape 3 du bootstrap).

Deux règles, et elles ne sont pas cosmétiques :

1. **Premier NON-VIDE gagne.** Un `KEY=` vide déclaré plus haut dans l'ordre de
   recherche ne masque pas un `KEY=valeur` déclaré plus bas. C'est le mode
   d'échec qui a déjà coûté un token Telegram : un doublon vide en tête de
   fichier écrasait silencieusement la vraie valeur via EnvironmentFile.

2. **N'override JAMAIS os.environ.** L'environnement réel du process prime
   toujours sur le fichier. Sans ça, un drill qui exporte JARVIS_HUB vers un
   port mort se ferait réécrire par le .env et ne prouverait rien.

API : load_env() -> dict · require(key) -> str · get(key, default) -> str|None
Stdlib-only.
"""

import os
from pathlib import Path

ROOT = Path(os.environ.get("JARVIS_ROOT", Path(__file__).resolve().parents[2]))

# Ordre de recherche figé. Documenté, pas découvert à l'exécution.
SEARCH_ORDER = [
    lambda: (
        Path(os.environ["JARVIS_ENV_FILE"])
        if os.environ.get("JARVIS_ENV_FILE")
        else None
    ),
    lambda: ROOT / ".env",
    lambda: ROOT / "config" / ".env",
    lambda: Path.home() / ".jarvis.env",
]

_CACHE = None


def _parse(path):
    """Parse un fichier .env. Retourne {} si illisible — jamais d'exception."""
    out = {}
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return out
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        # retire un seul niveau de quotes appariées
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
            val = val[1:-1]
        if key:
            out[key] = val
    return out


def load_env(refresh=False):
    """Fusionne les fichiers .env dans l'ordre. Premier non-vide gagne.

    Ne touche pas os.environ. Retourne le dict fusionné (fichiers uniquement).
    """
    global _CACHE
    if _CACHE is not None and not refresh:
        return dict(_CACHE)
    merged = {}
    for resolver in SEARCH_ORDER:
        try:
            path = resolver()
        except (KeyError, OSError):
            continue
        if not path or not path.is_file():
            continue
        for key, val in _parse(path).items():
            # premier NON-VIDE gagne : une valeur vide ne prend jamais la place
            # d'une valeur déjà retenue, et ne bloque pas une valeur ultérieure
            if val == "":
                merged.setdefault(key, "")
                continue
            if not merged.get(key):
                merged[key] = val
    _CACHE = merged
    return dict(merged)


def get(key, default=None):
    """Valeur effective : os.environ (non vide) d'abord, puis les fichiers."""
    live = os.environ.get(key)
    if live:
        return live
    val = load_env().get(key)
    return val if val else default


def require(key):
    """Comme get(), mais lève si la clé est absente ou vide. Jamais de valeur inventée."""
    val = get(key)
    if not val:
        raise KeyError(
            f"clé de configuration requise absente ou vide: {key} "
            f"(cherchée dans os.environ puis {', '.join(str(r()) for r in SEARCH_ORDER if r())})"
        )
    return val
