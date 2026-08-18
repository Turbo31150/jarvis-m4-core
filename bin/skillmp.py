#!/usr/bin/env python3
"""skillmp — CLI du catalogue SkillsMP (0 token, deterministe).

La cascade (`skillmp-cascade.sh`) dispatche en appelant `skillmp install <slug>`.
Cette commande n'existait nulle part : tous les dispatches echouaient en `failed`.
Ce module la fournit, sur le chemin de repli prevu par le script.

Sous-commandes : install · search · show · resolve

Resolution du slug — les URL SkillsMP finissent par un segment generique
("/skill"), si bien que 1 534 lignes du catalogue portent le slug "skill".
La file de cascade, elle, contient le slug LISIBLE derive de l'URL. On resout
donc d'abord sur le slug brut, puis en reconstruisant le slug lisible.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys

DB = os.path.expanduser("~/jarvis/jarvis_master.db")
CIBLE_CLAUDE = os.path.expanduser("~/.claude/plugins/local/skillsmp/skills")
CIBLE_OPENCLAW = os.path.expanduser("~/.openclaw/skills")
SLUGS_GENERIQUES = {"skill", "skills", "index", "main", "master", ""}


def slug_lisible(slug: str, url: str) -> str:
    brut = (slug or "").strip("/")
    if brut and brut not in SLUGS_GENERIQUES:
        return brut
    for seg in reversed([x for x in (url or "").split("/") if x]):
        if seg not in SLUGS_GENERIQUES and "." not in seg:
            return seg
    return brut or "sans-nom"


def connecte() -> sqlite3.Connection:
    cx = sqlite3.connect(DB)
    cx.row_factory = sqlite3.Row
    return cx


def resout(cx: sqlite3.Connection, cible: str) -> sqlite3.Row | None:
    """Trouve la ligne du catalogue correspondant a un slug brut ou lisible."""
    r = cx.execute(
        "SELECT * FROM skillsmp_skills WHERE slug = ? LIMIT 1", (cible,)
    ).fetchone()
    if r and slug_lisible(r["slug"], r["url"]) == cible:
        return r
    # slug lisible : l'URL contient le segment porteur juste avant "/skill"
    for motif in (f"%/{cible}/skill", f"%/{cible}", f"%/{cible}/%"):
        for cand in cx.execute(
            "SELECT * FROM skillsmp_skills WHERE url LIKE ? LIMIT 20", (motif,)
        ):
            if slug_lisible(cand["slug"], cand["url"]) == cible:
                return cand
    return r


def ecrit_skill_md(racine: str, slug: str, d: sqlite3.Row) -> str:
    dossier = os.path.join(racine, slug)
    os.makedirs(dossier, exist_ok=True)
    desc = (d["description"] or "").replace("\n", " ").strip()[:900]
    corps = d["corps"] or ""
    contenu = (
        "---\n"
        f"name: {slug}\n"
        f"description: {desc}\n"
        "---\n\n"
        f"# {d['nom']}\n\n"
        f"{desc}\n\n"
        f"- Depot : {d['repo']} ({d['repo_url']})\n"
        f"- Plateformes : {d['plateforme']}\n"
        f"- Installation : `{d['installation']}`\n"
        f"- Source SkillsMP : {d['url']}\n"
    )
    if corps:
        contenu += "\n---\n\n" + corps
    chemin = os.path.join(dossier, "SKILL.md")
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(contenu)
    return chemin


def cmd_install(a) -> int:
    cx = connecte()
    d = resout(cx, a.slug)
    if d is None:
        print(f"[skillmp] introuvable au catalogue : {a.slug}", file=sys.stderr)
        return 2
    slug = slug_lisible(d["slug"], d["url"])
    cibles = []
    if a.cible in ("both", "claude"):
        cibles.append(("claude", CIBLE_CLAUDE, "installe_claude"))
    if a.cible in ("both", "openclaw"):
        cibles.append(("openclaw", CIBLE_OPENCLAW, "installe_openclaw"))
    for nom, racine, colonne in cibles:
        chemin = ecrit_skill_md(racine, slug, d)
        cx.execute(
            f"UPDATE skillsmp_affectation SET {colonne}=1 WHERE url=?", (d["url"],)
        )
        print(f"[skillmp] {nom}: {chemin}")
    cx.commit()
    return 0


def cmd_search(a) -> int:
    cx = connecte()
    try:
        lignes = cx.execute(
            "SELECT s.slug, s.url, s.nom, s.description FROM skillsmp_fts f "
            "JOIN skillsmp_skills s ON s.rowid = f.rowid "
            "WHERE skillsmp_fts MATCH ? LIMIT ?",
            (a.requete, a.limite),
        ).fetchall()
    except sqlite3.OperationalError:
        motif = f"%{a.requete}%"
        lignes = cx.execute(
            "SELECT slug, url, nom, description FROM skillsmp_skills "
            "WHERE nom LIKE ? OR description LIKE ? LIMIT ?",
            (motif, motif, a.limite),
        ).fetchall()
    for r in lignes:
        print(f"{slug_lisible(r['slug'], r['url']):55s} {(r['nom'] or '')[:60]}")
    if not lignes:
        print("(aucun resultat)")
    return 0


def cmd_show(a) -> int:
    cx = connecte()
    d = resout(cx, a.slug)
    if d is None:
        print(f"[skillmp] introuvable : {a.slug}", file=sys.stderr)
        return 2
    for champ in ("nom", "url", "repo", "repo_url", "auteur", "langage",
                  "plateforme", "installation", "description"):
        val = d[champ]
        if val:
            print(f"{champ:14s}: {str(val)[:300]}")
    return 0


def cmd_resolve(a) -> int:
    cx = connecte()
    d = resout(cx, a.slug)
    if d is None:
        return 2
    print(slug_lisible(d["slug"], d["url"]))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="skillmp", description="CLI catalogue SkillsMP")
    sp = p.add_subparsers(dest="cmd", required=True)

    pi = sp.add_parser("install", help="ecrit le SKILL.md dans les cibles")
    pi.add_argument("slug")
    pi.add_argument("--cible", choices=["both", "claude", "openclaw"], default="both")
    pi.set_defaults(fn=cmd_install)

    ps = sp.add_parser("search", help="recherche FTS5 dans le catalogue")
    ps.add_argument("requete")
    ps.add_argument("--limite", type=int, default=20)
    ps.set_defaults(fn=cmd_search)

    ph = sp.add_parser("show", help="fiche d'un skill")
    ph.add_argument("slug")
    ph.set_defaults(fn=cmd_show)

    pr = sp.add_parser("resolve", help="slug brut -> slug lisible")
    pr.add_argument("slug")
    pr.set_defaults(fn=cmd_resolve)

    a = p.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
