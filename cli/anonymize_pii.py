#!/usr/bin/env python3
"""Anonymiseur PII — logique NER du projet service-aide-automatisation.

Détecte les données personnelles et les remplace par des tokens [PII_TYPE_N]
AVANT toute utilisation (bibliothèque, LLM cloud, partage). Le mapping inverse
reste LOCAL (jamais exporté) pour restitution éventuelle côté client.

Usage:
    from anonymize_pii import anonymize, restore
    clean, mapping = anonymize(texte)            # -> texte masqué + map locale
    original = restore(clean, mapping)           # restitution locale

CLI:
    python3 anonymize_pii.py fichier.txt         # imprime la version anonymisée
    echo "..." | python3 anonymize_pii.py -      # depuis stdin
"""

from __future__ import annotations

import re
import sys

# --- Détecteurs structurés (regex déterministes, ordre = priorité) -------------
# NIR = numéro de sécurité sociale : 13 chiffres + clé 2, avec espaces optionnels.
_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("NIR", re.compile(r"\b[12]\s?\d{2}\s?\d{2}\s?\d{2,3}\s?\d{3}\s?\d{3}\s?\d{2}\b")),
    ("IBAN", re.compile(r"\bFR\d{2}[ ]?(?:\d{4}[ ]?){5}\d{3}\b", re.I)),
    ("SIRET", re.compile(r"\b\d{3}[ ]?\d{3}[ ]?\d{3}[ ]?\d{5}\b")),
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("TEL", re.compile(r"\b0[1-9](?:[ .-]?\d{2}){4}\b")),
    (
        "DATE_NAISS",
        re.compile(
            r"\b(?:0[1-9]|[12]\d|3[01])[/.-](?:0[1-9]|1[0-2])[/.-](?:19|20)\d{2}\b"
        ),
    ),
    ("CP_VILLE", re.compile(r"\b\d{5}\s+[A-ZÉÈÀ][A-Za-zÉÈÀ'’\- ]{2,30}\b")),
]

# --- Noms/entités personnelles connus (extensible) -----------------------------
# La "logique NER" : on masque aussi les entités nommées non structurées.
# Liste de base (famille du dossier) — étendre via NER local si besoin.
_NAMES = [
    "Domingues",
    "Delmas",
    "Franck",
    "Claire",
    "Swan",
    "Lespinasse",
    "2 rue de l'Église",
    "rue de l'Eglise",
]


def _names_pattern() -> re.Pattern:
    parts = sorted({re.escape(n) for n in _NAMES if n.strip()}, key=len, reverse=True)
    return re.compile(r"(?<![\w])(" + "|".join(parts) + r")(?![\w])", re.I)


def anonymize(text: str, extra_names: list[str] | None = None) -> tuple[str, dict]:
    """Retourne (texte_anonymisé, mapping token->valeur). Mapping = LOCAL only."""
    mapping: dict[str, str] = {}
    counters: dict[str, int] = {}
    seen: dict[str, str] = {}  # valeur -> token (cohérence : même PII = même token)

    def _tok(kind: str, value: str) -> str:
        if value in seen:
            return seen[value]
        counters[kind] = counters.get(kind, 0) + 1
        token = f"[PII_{kind}_{counters[kind]}]"
        mapping[token] = value
        seen[value] = token
        return token

    out = text
    patterns = list(_PATTERNS)
    names = list(_NAMES) + (extra_names or [])
    if names:
        parts = sorted(
            {re.escape(n) for n in names if n.strip()}, key=len, reverse=True
        )
        patterns.append(
            ("NOM", re.compile(r"(?<![\w])(" + "|".join(parts) + r")(?![\w])", re.I))
        )

    for kind, pat in patterns:
        out = pat.sub(lambda m: _tok(kind, m.group(0)), out)
    return out, mapping


def restore(text: str, mapping: dict) -> str:
    """Restitution LOCALE : réinjecte les valeurs d'origine."""
    for token, value in mapping.items():
        text = text.replace(token, value)
    return text


def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    src = (
        sys.stdin.read()
        if argv[1] == "-"
        else open(argv[1], encoding="utf-8", errors="replace").read()
    )
    clean, mapping = anonymize(src)
    sys.stdout.write(clean)
    sys.stderr.write(f"\n[anonymize] {len(mapping)} entités PII masquées\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
