#!/usr/bin/env python3
"""Todolist massive unifiée pour M4 — agrège toutes les sources de travail réel.

Remplace ~/jarvis/bin/planning-mega.py, qui venait de M1 et n'existe pas ici :
la skill run-planning-autogen le référence encore, d'où son échec.

Sources fusionnées :
  1. TODO / FIXME / XXX du code (jarvis, Bureau, labo)
  2. cases « - [ ] » non cochées des .md
  3. dépôts git avec des modifications non commitées
  4. unités systemd en échec (system + user)
  5. chantiers business : formations non rédigées / non livrées dans Notion
  6. dette d'infrastructure mesurée (couverture vectorielle du board, nœuds morts)

Chaque tâche reçoit un préchargement biblio : le bloc de BLOCS-INDEX.tsv dont
les mots-clés recoupent le mieux le titre. Sans lui, l'exécutant repart de zéro
sur un savoir déjà écrit.

Écrit dans jarvis_master.db (table tasks) → visible dans le widget :8899.
Dédup contre le PENDING courant seulement : une tâche résolue puis revenue
doit pouvoir réapparaître. stdlib uniquement, 0 token.

Usage : planning_mega_m4.py [--dry] [--no-preload] [--cap N]
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
MASTER_DB = HOME / "jarvis/jarvis_master.db"
BLOCS = HOME / "labo/bibliotheque/lib/BLOCS-INDEX.tsv"
BOARD_DB = HOME / "jarvis/board/board.db"
FORMATIONS_DB = HOME / "jarvis/data/formations_contenu.db"

RACINES_CODE = [HOME / "jarvis", HOME / "Bureau", HOME / "labo"]
EXCLUS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".cache",
    "site-packages",
    "dist",
    "build",
    ".mypy_cache",
    ".ruff_cache",
}
CAP_DEFAUT = 600
MOTS_VIDES = {
    "pour",
    "avec",
    "dans",
    "les",
    "des",
    "une",
    "sur",
    "que",
    "qui",
    "est",
    "par",
    "aux",
    "cette",
    "plus",
    "tout",
    "the",
    "and",
    "for",
    "this",
}


# ────────────────────────────── collecte ──────────────────────────────


def _fichiers(racine: Path, motifs: tuple[str, ...], plafond: int = 4000):
    if not racine.exists():
        return
    vus = 0
    for p in racine.rglob("*"):
        if vus >= plafond:
            return
        if not p.is_file() or p.suffix not in motifs:
            continue
        if any(part in EXCLUS for part in p.parts):
            continue
        vus += 1
        yield p


def taches_todo_code() -> list[tuple[str, str, str]]:
    """TODO/FIXME/XXX laissés dans le code."""
    out, motif = [], re.compile(r"#\s*(TODO|FIXME|XXX)\s*:?\s*(.{6,150})")
    for racine in RACINES_CODE:
        for p in _fichiers(racine, (".py", ".sh", ".js", ".ts")):
            try:
                texte = p.read_text(errors="ignore")
            except OSError:
                continue
            for n, ligne in enumerate(texte.splitlines()[:600], 1):
                m = motif.search(ligne)
                if m:
                    libelle = m.group(2).strip().rstrip("\"'`")
                    out.append(
                        (
                            f"[code] {libelle[:120]}",
                            f"{p}:{n} — marqueur {m.group(1)}",
                            "dev",
                        )
                    )
    return out


def taches_cases_md() -> list[tuple[str, str, str]]:
    """Cases « - [ ] » non cochées dans les notes markdown."""
    out, motif = [], re.compile(r"^\s*[-*]\s*\[ \]\s+(.{6,150})")
    for racine in RACINES_CODE:
        for p in _fichiers(racine, (".md",), plafond=2500):
            try:
                texte = p.read_text(errors="ignore")
            except OSError:
                continue
            for ligne in texte.splitlines()[:400]:
                m = motif.match(ligne)
                if m:
                    out.append(
                        (
                            f"[note] {m.group(1).strip()[:120]}",
                            f"{p} — case non cochée",
                            "misc-ops",
                        )
                    )
    return out


def taches_git_sales() -> list[tuple[str, str, str]]:
    """Dépôts porteurs de modifications non commitées."""
    out = []
    for racine in RACINES_CODE:
        if not racine.exists():
            continue
        for git in list(racine.rglob(".git"))[:60]:
            depot = git.parent
            try:
                r = subprocess.run(
                    ["git", "-C", str(depot), "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
            except (subprocess.SubprocessError, OSError):
                continue
            n = len([x for x in r.stdout.splitlines() if x.strip()])
            if n:
                out.append(
                    (
                        f"[git] committer {n} modification(s) — {depot.name}",
                        f"{depot} — {n} fichier(s) non commité(s)",
                        "dev",
                    )
                )
    return out


def taches_services() -> list[tuple[str, str, str]]:
    """Unités systemd en échec, système et utilisateur."""
    out = []
    for portee in (["systemctl"], ["systemctl", "--user"]):
        try:
            r = subprocess.run(
                portee + ["list-units", "--state=failed", "--no-legend", "--plain"],
                capture_output=True,
                text=True,
                timeout=25,
            )
        except (subprocess.SubprocessError, OSError):
            continue
        for ligne in r.stdout.splitlines():
            unite = ligne.split()[0] if ligne.split() else ""
            if unite:
                out.append(
                    (
                        f"[infra] réparer l'unité en échec {unite}",
                        f"systemd {'--user' if '--user' in portee else 'system'} — état failed",
                        "ops-sre",
                    )
                )
    return out


def taches_business() -> list[tuple[str, str, str]]:
    """Formations non rédigées ou non livrées dans Notion."""
    if not FORMATIONS_DB.exists():
        return []
    c = sqlite3.connect(f"file:{FORMATIONS_DB}?mode=ro", uri=True)
    out = []
    for slug, titre, prix in c.execute(
        "SELECT slug,titre,prix FROM contenu WHERE markdown IS NULL ORDER BY prix DESC"
    ):
        out.append(
            (
                f"[business] rédiger la formation « {titre[:90]} » ({prix} €)",
                f"slug {slug} — contenu absent, pipeline notion_formations_pipeline.py",
                "business-ops",
            )
        )
    for slug, titre in c.execute(
        "SELECT slug,titre FROM contenu WHERE markdown IS NOT NULL AND notion_page_id IS NULL"
    ):
        out.append(
            (
                f"[business] livrer dans Notion « {titre[:90]} »",
                f"slug {slug} — rédigée mais pas encore poussée",
                "business-ops",
            )
        )
    c.close()
    return out


def taches_dette_infra() -> list[tuple[str, str, str]]:
    """Dette mesurée, pas supposée : couverture vectorielle réelle du board."""
    out = []
    if BOARD_DB.exists():
        c = sqlite3.connect(f"file:{BOARD_DB}?mode=ro", uri=True)
        for dom, tot, vect in c.execute(
            "SELECT domain_id, COUNT(*), SUM(embedding IS NOT NULL) "
            "FROM chunks GROUP BY 1"
        ):
            taux = (vect or 0) / tot if tot else 0
            # Sous 60 %, board.py sert le domaine en BM25 seul : la voie
            # vectorielle est desactivee, pas degradee.
            if taux < 0.60:
                out.append(
                    (
                        f"[board] vectoriser le domaine {dom} — {taux:.0%} couvert",
                        f"{tot - (vect or 0)} chunks en attente ; sous 60 % la "
                        f"recherche tombe en BM25 seul",
                        "data-pipeline",
                    )
                )
        c.close()
    return out


# ────────────────────────────── biblio ──────────────────────────────


def charger_blocs() -> list[tuple[str, set, str]]:
    if not BLOCS.exists():
        return []
    blocs = []
    for ligne in BLOCS.read_text(errors="ignore").splitlines()[1:]:
        ch = ligne.split("\t")
        if len(ch) < 4:
            continue
        mots = {m for m in re.findall(r"\w{4,}", ch[2].lower()) if m not in MOTS_VIDES}
        if mots:
            blocs.append((ch[0], mots, ch[3][:400]))
    return blocs


def precharger(titre: str, blocs) -> str | None:
    """Bloc dont les mots-clés recoupent le mieux le titre."""
    mots = {m for m in re.findall(r"\w{4,}", titre.lower()) if m not in MOTS_VIDES}
    if not mots:
        return None
    meilleur, score_max = None, 1  # 1 mot commun ne prouve rien : on exige 2
    for bloc_id, cles, action in blocs:
        score = len(mots & cles)
        if score > score_max:
            meilleur, score_max = f"[{bloc_id}] {action}", score
    return meilleur


# ────────────────────────────── écriture ──────────────────────────────


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="simulation, aucune écriture")
    ap.add_argument("--no-preload", action="store_true")
    ap.add_argument("--cap", type=int, default=CAP_DEFAUT)
    args = ap.parse_args()

    if not MASTER_DB.exists():
        sys.exit(f"base absente : {MASTER_DB}")

    # Quota par source. Sans lui, les 2 459 cases « - [ ] » des notes — dont
    # beaucoup dorment dans des archives — consomment tout le plafond et
    # repoussent hors file les pannes de service et le business. L'ordre vaut
    # priorité : ce qui bloque la production passe avant ce qui traîne.
    sources = [
        ("services en échec", taches_services, 50),
        ("dette board", taches_dette_infra, 20),
        ("business", taches_business, 120),
        ("git", taches_git_sales, 40),
        ("TODO code", taches_todo_code, 80),
        ("cases markdown", taches_cases_md, 200),
    ]
    toutes: list[tuple[str, str, str]] = []
    for nom, fn, quota in sources:
        try:
            lot = fn()
        except Exception as exc:  # noqa: BLE001 — une source cassée n'annule pas les autres
            print(f"  ! source « {nom} » hors service : {exc}")
            lot = []
        garde = lot[:quota]
        laisse = len(lot) - len(garde)
        suffixe = f"  (+{laisse} hors quota)" if laisse else ""
        print(f"  {nom:20s} → {len(garde)}{suffixe}")
        toutes.extend(garde)

    conn = sqlite3.connect(MASTER_DB, timeout=30)
    pending = {
        t
        for (t,) in conn.execute(
            "SELECT title FROM tasks WHERE status IN ('pending','running','in_progress')"
        )
    }
    neuves, vus = [], set()
    for titre, ctx, agent in toutes:
        if titre in pending or titre in vus:
            continue
        vus.add(titre)
        neuves.append((titre, ctx, agent))

    tronque = len(neuves) > args.cap
    if tronque:
        print(
            f"  ⚠ plafond {args.cap} : {len(neuves) - args.cap} tâche(s) non insérée(s)"
        )
        neuves = neuves[: args.cap]

    blocs = [] if args.no_preload else charger_blocs()
    if blocs:
        print(f"  biblio chargée      → {len(blocs)} blocs")

    if args.dry:
        print(f"\n[simulation] {len(neuves)} tâche(s) seraient insérées")
        for titre, _, agent in neuves[:15]:
            print(f"   · ({agent}) {titre[:100]}")
        conn.close()
        return

    inserees = 0
    for titre, ctx, agent in neuves:
        preload = precharger(titre, blocs) if blocs else None
        conn.execute(
            "INSERT INTO tasks(title,context,status,agent,machine,biblio_preload) "
            "VALUES(?,?,'pending',?,'M4',?)",
            (titre, ctx, agent, preload),
        )
        inserees += 1
    conn.commit()
    total = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE status='pending'"
    ).fetchone()[0]
    conn.close()
    print(f"\n✓ {inserees} tâche(s) insérée(s) — file pending : {total}")


if __name__ == "__main__":
    main()
