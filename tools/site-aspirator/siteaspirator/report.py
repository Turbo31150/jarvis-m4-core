"""report.py — Génération du rapport d'extraction (json + markdown + Mermaid).

Consomme l'index/navigation/historique écrits par memory.py et produit :
  rapport.json  — données brutes consolidées
  rapport.md    — rapport lisible + diagramme Mermaid du parcours
"""

import json
from pathlib import Path


def _mermaid(edges, index):
    """Arbre de navigation en Mermaid (graph LR)."""
    title = {p["url"]: p["title"] or p["slug"] for p in index}
    seen, lines = set(), ["```mermaid", "graph LR"]
    for e in edges[:60]:
        a, b = e["from"], e["to"]
        na = title.get(a, a)[:24].replace('"', "'")
        nb = title.get(b, b)[:24].replace('"', "'")
        key = (a, b)
        if key in seen:
            continue
        seen.add(key)
        lines.append(f'  "{na}" --> "{nb}"')
    lines.append("```")
    return "\n".join(lines)


def build(session_dir):
    d = Path(session_dir)
    index = json.loads((d / "index.json").read_text(encoding="utf-8"))
    nav = json.loads((d / "navigation.json").read_text(encoding="utf-8"))
    hist = json.loads((d / "historique.json").read_text(encoding="utf-8"))
    edges = nav.get("edges", [])

    consolidated = {
        "session": d.name,
        "pages_count": len(index),
        "edges_count": len(edges),
        "actions_count": len(hist),
        "pages": index,
    }
    (d / "rapport.json").write_text(
        json.dumps(consolidated, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    total_nodes = sum(p.get("nodes", 0) for p in index)
    md = [
        f"# Rapport d'extraction — {d.name}",
        "",
        f"- Pages avalées : **{len(index)}**",
        f"- Nœuds DOM cumulés : **{total_nodes}**",
        f"- Liens de navigation : **{len(edges)}**",
        f"- Actions journalisées : **{len(hist)}**",
        "",
        "## Pages",
        "",
        "| # | Titre | Nœuds | Nav | Liens | Slug |",
        "|---|---|---|---|---|---|",
    ]
    for i, p in enumerate(index, 1):
        md.append(
            f"| {i} | {(p['title'] or '(sans titre)')[:40]} | {p['nodes']} "
            f"| {p['nav']} | {p['links']} | `{p['slug']}` |"
        )
    md += ["", "## Arbre de navigation", "", _mermaid(edges, index), ""]
    (d / "rapport.md").write_text("\n".join(md), encoding="utf-8")
    return {"json": str(d / "rapport.json"), "md": str(d / "rapport.md")}
