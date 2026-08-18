"""memory.py — Mémorisation locale : sauvegarde le code source extrait + les métadonnées.

Arborescence produite par session :
  <out>/<session>/
    pages/<slug>/index.html      (code source HTML avalé)
    pages/<slug>/capture.json     (nav + ressources + dom + events)
    pages/<slug>/shot.png         (capture d'état, optionnelle)
    index.json                    (index des pages)
    navigation.json               (graphe des liens = parcours)
    historique.json               (chronologie des actions)
    logs.jsonl                    (journal d'exécution)
"""

import json
import re
import hashlib
from pathlib import Path


def slugify(url):
    s = re.sub(r"^https?://", "", url or "page")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-")[:60] or "page"
    h = hashlib.sha1((url or "").encode()).hexdigest()[:6]
    return f"{s}-{h}"


class Memory:
    def __init__(self, out_dir, session):
        self.root = Path(out_dir) / session
        (self.root / "pages").mkdir(parents=True, exist_ok=True)
        self.index = []  # [{slug,url,title,nodes,links}]
        self.nav_edges = []  # [{from,to}]
        self.history = []  # chronologie des actions
        self._log_fp = (self.root / "logs.jsonl").open("a", encoding="utf-8")

    # --- journal ---
    def log(self, step, **kw):
        rec = {"step": step, **kw}
        self._log_fp.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self._log_fp.flush()
        self.history.append(rec)

    # --- sauvegarde d'une page avalée ---
    def save_page(self, url, cap, shot=None):
        slug = slugify(url)
        pdir = self.root / "pages" / slug
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / "index.html").write_text(cap.get("html", ""), encoding="utf-8")
        meta_copy = {k: v for k, v in cap.items() if k != "html"}
        (pdir / "capture.json").write_text(
            json.dumps(meta_copy, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        if shot:
            (pdir / "shot.png").write_bytes(shot)
        self.index.append(
            {
                "slug": slug,
                "url": url,
                "title": cap.get("meta", {}).get("title", ""),
                "nodes": cap.get("dom", {}).get("nodes", 0),
                "nav": len(cap.get("navigation", [])),
                "links": len(cap.get("links", [])),
            }
        )
        for target in cap.get("links", []):
            self.nav_edges.append({"from": url, "to": target})
        return slug

    # --- clôture : écrit index / navigation / historique ---
    def flush(self):
        (self.root / "index.json").write_text(
            json.dumps(self.index, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (self.root / "navigation.json").write_text(
            json.dumps({"edges": self.nav_edges}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (self.root / "historique.json").write_text(
            json.dumps(self.history, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self._log_fp.close()
        return self.root
