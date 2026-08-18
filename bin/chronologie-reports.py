#!/usr/bin/env python3
"""chronologie-reports.py — construit une CHRONOLOGIE (0-token) des reports JARVIS.

Sources :
  1. ~/labo/bibliotheque/lib/report-turbo31150-blocs.tsv  (4179 reports indexés :
     nom<TAB>source<TAB>danger<TAB>bloc où bloc = `xdg-open '<path>'  # <titre>`)
  2. ~/jarvis/data/biblio_knowledge/*.md  (docs de connaissance datés)

Extrait une DATE par entrée (motif du nom/chemin, sinon mtime du fichier cible),
trie chronologiquement, écrit :
  - CHRONOLOGIE.md         (timeline lisible, groupée par jour)
  - chronologie.json       (pour ingestion jarvis-plan : {date,titre,path,source})
"""

import json
import os
import re
import sys

HOME = os.path.expanduser("~")
TSV = os.path.join(HOME, "labo/bibliotheque/lib/report-turbo31150-blocs.tsv")
KNOW = os.path.join(HOME, "jarvis/data/biblio_knowledge")
OUT_MD = (
    sys.argv[1]
    if len(sys.argv) > 1
    else os.path.join(HOME, "jarvis/data/CHRONOLOGIE.md")
)
OUT_JSON = os.path.splitext(OUT_MD)[0] + ".json"

DATE_RES = [
    (
        re.compile(r"(20\d{2})[-_]?(\d{2})[-_]?(\d{2})"),
        lambda m: f"{m.group(1)}-{m.group(2)}-{m.group(3)}",
    ),
]


def extract_date(text, path=None):
    for rx, fmt in DATE_RES:
        m = rx.search(text)
        if m:
            try:
                y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
                if 2020 <= y <= 2035 and 1 <= mo <= 12 and 1 <= d <= 31:
                    return fmt(m)
            except Exception:
                pass
    if path and os.path.exists(path):
        try:
            import datetime

            ts = os.path.getmtime(path)
            return datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
        except Exception:
            pass
    return "0000-00-00"  # sans date → en tête, à trier à part


def parse_bloc(bloc):
    """`xdg-open '<path>'  # <titre>` → (path, titre)."""
    path, titre = "", ""
    m = re.search(r"xdg-open\s+'([^']+)'", bloc)
    if m:
        path = m.group(1)
    m2 = re.search(r"#\s*(.+)$", bloc)
    if m2:
        titre = m2.group(1).strip()
    return path, titre


def main():
    entries = []
    # 1. TSV des reports GitHub/local indexés
    if os.path.exists(TSV):
        for line in open(TSV, encoding="utf-8", errors="replace"):
            cols = line.rstrip("\n").split("\t")
            if len(cols) < 4 or cols[1] == "source":
                continue
            nom, bloc = cols[0], cols[3]
            path, titre = parse_bloc(bloc)
            titre = titre or nom
            date = extract_date(nom + " " + path + " " + titre, path)
            entries.append(
                {"date": date, "titre": titre[:120], "path": path, "source": "report"}
            )
    # 2. docs de connaissance datés
    if os.path.isdir(KNOW):
        for fn in os.listdir(KNOW):
            if not fn.endswith(".md"):
                continue
            p = os.path.join(KNOW, fn)
            date = extract_date(fn, p)
            entries.append(
                {"date": date, "titre": fn[:-3][:120], "path": p, "source": "knowledge"}
            )

    entries.sort(key=lambda e: e["date"])
    dated = [e for e in entries if e["date"] != "0000-00-00"]
    undated = [e for e in entries if e["date"] == "0000-00-00"]

    # JSON pour jarvis-plan
    json.dump(entries, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False)

    # Markdown timeline groupé par jour (uniquement les datés, plus lisible)
    L = [
        "# 🕰 Chronologie JARVIS — reports & documents\n",
        f"{len(entries)} entrées ({len(dated)} datées · {len(undated)} sans date) — source déterministe 0-token.\n",
    ]
    cur = None
    for e in dated:
        if e["date"] != cur:
            cur = e["date"]
            L.append(f"\n## {cur}")
        L.append(f"- **{e['titre']}**  ·  `{e['source']}`  ·  `{e['path']}`")
    L.append(f"\n---\n### Sans date ({len(undated)})\n")
    for e in undated[:200]:
        L.append(f"- {e['titre']}  ·  `{e['source']}`")
    if len(undated) > 200:
        L.append(f"- … +{len(undated) - 200} autres")
    open(OUT_MD, "w", encoding="utf-8").write("\n".join(L) + "\n")

    print(
        f"OK — {len(entries)} entrées ({len(dated)} datées, {len(undated)} sans date)"
    )
    print(f"     {OUT_MD}")
    print(f"     {OUT_JSON}")
    if dated:
        print(f"     plage: {dated[0]['date']} → {dated[-1]['date']}")


if __name__ == "__main__":
    main()
