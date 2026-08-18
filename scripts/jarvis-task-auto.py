#!/usr/bin/env python3
"""jarvis-task-auto.py — auto-traitement des tâches via le dispatcher mots-clés.

Prend les tâches `pending` de la table `tasks` (jarvis_master.db), route chacune
via jarvis-keyword-dispatch.py (détection mots-clés → lane hub / CLI gratuit /
domino / outil), enregistre le résultat dans data/task_results/<id>.md, marque `done`.
Garde-fous : LIMIT par run, timeout par tâche, log. 0 token Anthropic (cluster gratuit).

Usage :
  jarvis-task-auto.py [--limit N] [--dry]
"""

import os
import sys
import json
import sqlite3
import subprocess
import datetime

ROOT = os.path.expanduser("~/jarvis")
DB = os.environ.get("JARVIS_DB", f"{ROOT}/jarvis_master.db")
DISPATCH = f"{ROOT}/scripts/jarvis-keyword-dispatch.py"
RESULTS = f"{ROOT}/data/task_results"
LOG = f"{ROOT}/data/task-auto.log"
LIMIT = 3
TIMEOUT = 300


def log(m):
    line = f"{datetime.datetime.now().isoformat(timespec='seconds')} {m}"
    print(line)
    try:
        open(LOG, "a", encoding="utf-8").write(line + "\n")
    except Exception:
        pass


# ─── exécution RÉELLE et SÛRE (SANS shell → pas d'injection possible) ───
# On NE bash-c PAS le ready_cmd stocké (il contient $(...) = substitution =
# injection). On dérive le type depuis le domaine du contexte + un argument
# STRICTEMENT validé, et on lance des commandes fixes en forme LISTE (no shell).
import re as _re

_HOME = os.path.expanduser("~")
_NAME_OK = _re.compile(r"^[A-Za-z0-9._-]{1,64}$")  # repo : chars sûrs uniquement
_SVC_OK = _re.compile(r"^[A-Za-z0-9._@-]{1,80}$")  # unité systemd


def _run_list(argv, timeout=20):
    """Exécute une commande en forme LISTE (jamais de shell)."""
    r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    return (r.stdout + r.stderr).strip()


def _execute_task(title, ctx):
    """Exécute RÉELLEMENT une tâche mécanique, sans shell. Renvoie la sortie
    réelle, ou None si la tâche n'est pas d'un type auto-exécutable sûr."""
    ctx = ctx or ""
    title = title or ""
    try:
        # git : "…dans REPO"  → git -C <path résolu> status (read-only)
        if "[git]" in ctx:
            m = _re.search(r"dans\s+([A-Za-z0-9._-]+)", title)
            if not m or not _NAME_OK.match(m.group(1)):
                return None
            repo = m.group(1)
            path = _run_list(
                ["find", _HOME, "-maxdepth", "4", "-name", repo, "-type", "d"], 15
            ).splitlines()
            if not path:
                return f"[EXÉCUTÉ] repo '{repo}' introuvable"
            out = _run_list(["git", "-C", path[0], "status"], 15)
            return f"[EXÉCUTÉ RÉELLEMENT — pas du LLM]\n▶ git -C {path[0]} status\n\n{out[:3500]}"
        # incident : "…service SVC" → systemctl status + journalctl (read-only)
        if "[incident]" in ctx:
            m = _re.search(r"service\s+([A-Za-z0-9._@-]+)", title)
            if not m or not _SVC_OK.match(m.group(1)):
                return None
            svc = m.group(1)
            st = _run_list(["systemctl", "--user", "status", svc, "--no-pager"], 12)
            jl = _run_list(
                ["journalctl", "--user", "-u", svc, "-n", "20", "--no-pager"], 12
            )
            return (
                f"[EXÉCUTÉ RÉELLEMENT — pas du LLM]\n▶ status+journal {svc}\n\n"
                f"{st[:1800]}\n---\n{jl[:1800]}"
            )
    except Exception as e:
        return f"[exécution sûre échouée: {e}]"
    return None


_ROUTES_FILE = os.path.expanduser("~/jarvis/data/source_routes.json")
_routes_cache = None


def _route_source(title):
    """Classifie une tâche → (source, flux) via source_routes.json. Rapide, sans effet."""
    global _routes_cache
    if _routes_cache is None:
        try:
            _routes_cache = json.load(open(_ROUTES_FILE, encoding="utf-8"))
        except Exception:
            _routes_cache = {
                "rules": [],
                "default": {"source": "mcp", "flux": "execution"},
            }
    low = (title or "").lower()
    for r in _routes_cache.get("rules", []):
        for kw in r.get("keywords", []):
            if kw in low:
                return r["source"], r["flux"]
    d = _routes_cache.get("default", {"source": "mcp", "flux": "execution"})
    return d["source"], d["flux"]


def main(argv):
    dry = "--dry" in argv
    limit = LIMIT
    if "--limit" in argv:
        try:
            limit = int(argv[argv.index("--limit") + 1])
        except Exception:
            pass
    os.makedirs(RESULTS, exist_ok=True)
    # 120 s : à 8 s puis 30 s, ce script abandonnait le premier de tous les
    # écrivains concurrents et mourait en "sqlite3.OperationalError: database
    # is locked" — reproduit déterministement en tenant un verrou
    # BEGIN IMMEDIATE. La base est en WAL (un seul écrivain à la fois) et
    # plusieurs producteurs permanents y écrivent en continu.
    # Les deux réglages sont nécessaires : timeout= ne couvre pas tous les
    # chemins du driver, le PRAGMA vaut pour toute la connexion.
    c = sqlite3.connect(DB, timeout=120)
    c.execute("PRAGMA busy_timeout=120000")
    rows = c.execute(
        # priorise les tâches RÉELLEMENT exécutables (avec ▶ ready_cmd) avant le reste
        "SELECT id, title, context FROM tasks WHERE status='pending' "
        "ORDER BY (context LIKE '%▶%') DESC, id LIMIT ?",
        (limit,),
    ).fetchall()
    if not rows:
        log("[task-auto] aucune tâche pending")
        c.close()
        return 0
    log(f"[task-auto] {len(rows)} tâche(s) pending à router (dry={dry})")
    for tid, title, ctx in rows:
        title = title or ""
        # Route explicite portée par la tâche (context.route, ex: OMEGA-cascade)
        # → passe le keyword-matching, atteint directement son backend.
        route = None
        try:
            route = (json.loads(ctx) or {}).get("route") if ctx else None
        except Exception:
            route = None
        route_args = ["--route", route] if route else []
        if dry:
            r = subprocess.run(
                ["python3", DISPATCH, "--dry", *route_args, title],
                capture_output=True,
                text=True,
                timeout=30,
            )
            log(f"  #{tid} DRY {r.stdout.strip()}")
            continue
        # 1) tâche mécanique → EXÉCUTION RÉELLE et SÛRE (sans shell)
        out = _execute_task(title, ctx)
        if out is None:
            # 2) sinon → dispatch mots-clés (LLM/lane/domino)
            try:
                r = subprocess.run(
                    ["python3", DISPATCH, *route_args, title],
                    capture_output=True,
                    text=True,
                    timeout=TIMEOUT,
                )
                out = r.stdout.strip() or r.stderr.strip()
            except subprocess.TimeoutExpired:
                out = "[task-auto] timeout"
        # score qualité 0-1 (heuristique sur le résultat produit)
        low = out.lower()
        if "timeout" in low or "erreur" in low or "error" in low:
            score = 0.3
        elif "via " in out or len(out) > 300:  # vraie réponse LLM substantielle
            score = 0.9
        elif out.strip():
            score = 0.7
        else:
            score = 0.2
        # COUCHE ROUTAGE : tag la source/flux (classification seule, pas d'exécution
        # outward ici — l'exécution réelle par source = jarvis-source-router --go).
        src, flux = _route_source(title)
        route_tag = f"→ ROUTAGE: {src}/{flux}"
        # E1 : action OUTWARD (github/telegram/gtasks/notion/youtube) → statut
        # 'to_validate' (nécessite un --go humain via source-router), PAS 'done'.
        outward = src in ("github", "telegram", "gtasks", "notion", "youtube")
        final_status = "to_validate" if outward else "done"
        if outward:
            route_tag += "  [À VALIDER → jarvis-source-router --go --task ...]"
        # persiste le résultat + marque statut + score
        open(os.path.join(RESULTS, f"{tid}.md"), "w", encoding="utf-8").write(
            f"# Task #{tid}: {title}\n\n{route_tag}\n\n{out}\n"
        )
        for attempt in range(5):
            try:
                conn_up = sqlite3.connect(DB, timeout=120)
                conn_up.execute("PRAGMA busy_timeout=120000")
                conn_up.execute(
                    "UPDATE tasks SET status=?, score=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (final_status, score, tid),
                )
                conn_up.commit()
                conn_up.close()
                break
            except sqlite3.OperationalError as err:
                if attempt == 4:
                    log(f"  #{tid} UPDATE error: {err}")
                import time; time.sleep(2)
        first = out.splitlines()[0] if out else ""
        log(f"  #{tid} → {final_status} ({first[:70]})")
    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
