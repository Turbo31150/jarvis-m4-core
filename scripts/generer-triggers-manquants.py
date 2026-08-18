#!/usr/bin/env python3
"""Génère les entrées de déclenchement manquantes pour les skills run-* du dépôt.

Source de vérité des mots-clés : la ligne `description:` de chaque SKILL.md.
Beaucoup contiennent déjà une liste explicite (« Triggers FR/EN — "x", "y" ») —
on l'extrait telle quelle plutôt que d'inventer. Sinon, on retombe sur les
termes saillants de la description.

Idempotent : ne touche jamais aux entrées existantes, n'ajoute que les absentes.
"""

import json
import re
import shutil
import sys
from pathlib import Path

TRIGGERS = Path.home() / "jarvis/.claude/skills/run-jarvis-autoheal/skill-triggers.json"
SKILL_DIRS = [Path.home() / "jarvis/.claude/skills"]

# Mots vides : trop génériques pour discriminer un skill d'un autre.
STOP = {
    "the",
    "and",
    "for",
    "with",
    "use",
    "when",
    "this",
    "that",
    "from",
    "into",
    "run",
    "runs",
    "used",
    "using",
    "user",
    "asks",
    "ask",
    "via",
    "les",
    "des",
    "une",
    "aux",
    "sur",
    "pour",
    "avec",
    "dans",
    "est",
    "sont",
    "que",
    "qui",
    "par",
    "son",
    "ses",
    "the",
    "its",
    "and",
    "all",
    "any",
    "not",
    "you",
    "jarvis",
    "claude",
    "skill",
    "smoke",
    "test",
    "build",
    "drive",
    "start",
}


def read_description(text: str) -> str:
    """Extrait la description du frontmatter, y compris les scalaires YAML
    repliés (`>-`, `>`, `|`, `|-`) dont le contenu est sur les lignes suivantes."""
    m = re.search(r"^description:[ \t]*(.*)$", text, re.MULTILINE)
    if not m:
        return ""
    head = m.group(1).strip()
    if head not in (">-", ">", "|", "|-", ""):
        return head.strip('"')
    # Scalaire multi-ligne : on collecte les lignes indentées qui suivent.
    lines = text[m.end() :].splitlines()
    body = []
    for ln in lines[1:] if lines and not lines[0].strip() else lines:
        if ln.strip() and not ln.startswith((" ", "\t")):
            break  # retour au niveau du frontmatter → fin du bloc
        body.append(ln.strip())
    return " ".join(x for x in body if x).strip()


def extract_keywords(desc: str) -> tuple[list[str], list[str]]:
    """Retourne (fr, en). Priorité aux triggers cités entre guillemets."""
    quoted = re.findall(r'"([^"]{3,40})"', desc)
    quoted = [q.strip().lower() for q in quoted if not q.startswith("http")]

    # Un mot-clé accentué ou contenant un mot français courant part en FR.
    fr_markers = re.compile(
        r"[àâçéèêëîïôùûü]|\b(le|la|les|du|des|un|une|est|sur|"
        r"pour|avec|dans|quoi|comment|lance|relance|vérifie|"
        r"affiche|montre|ouvre|ferme|répond|marche|panne)\b"
    )
    fr = [q for q in quoted if fr_markers.search(q)]
    en = [q for q in quoted if q not in fr]

    if not quoted:
        # Repli : termes saillants (≥4 lettres, hors mots vides), dédupliqués.
        words, seen = [], set()
        for w in re.findall(r"[a-zA-Zàâçéèêëîïôùûü-]{4,}", desc.lower()):
            if w in STOP or w in seen:
                continue
            seen.add(w)
            words.append(w)
        fr, en = words[:6], words[:6]

    # Bornes : assez pour matcher, pas au point de déclencher à tort.
    return fr[:8], en[:8]


def main() -> int:
    if not TRIGGERS.exists():
        print(f"ABSENT : {TRIGGERS}", file=sys.stderr)
        return 1

    data = json.loads(TRIGGERS.read_text(encoding="utf-8"))
    existing = {t["skill"] for t in data.get("triggers", [])}

    added = []
    for base in SKILL_DIRS:
        for d in sorted(base.glob("run-*")):
            md = d / "SKILL.md"
            if not d.is_dir() or not md.exists() or d.name in existing:
                continue
            desc = read_description(md.read_text(encoding="utf-8", errors="replace"))
            if not desc:
                desc = d.name.replace("-", " ")
            fr, en = extract_keywords(desc)
            if not fr and not en:
                print(f"  IGNORÉ (aucun mot-clé exploitable) : {d.name}")
                continue
            # priority 5 : sous les entrées réglées à la main (7-8), qui gardent la priorité.
            data["triggers"].append(
                {"skill": d.name, "priority": 5, "keywords_fr": fr, "keywords_en": en}
            )
            added.append(d.name)

    if not added:
        print("Rien à ajouter — tous les skills run-* ont déjà un déclencheur.")
        return 0

    shutil.copy2(TRIGGERS, TRIGGERS.with_suffix(".json.bak"))
    data["triggers"].sort(key=lambda t: (-t.get("priority", 0), t["skill"]))
    TRIGGERS.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"ajoutés : {len(added)}")
    for n in added:
        print(f"  + {n}")
    print(f"total triggers : {len(data['triggers'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
