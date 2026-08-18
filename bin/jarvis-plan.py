#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jarvis-plan.py — PLANNING UNIFIÉ JARVIS (todolist dynamique + préchargement).

Fusionne TOUTES les sources de tâches JARVIS en une todolist unique indexée dans
une base overlay DÉDIÉE (~/jarvis/data/unified_plan.db, SQLite WAL, créée ici),
avec PRÉCHARGEMENT du contexte de chaque tâche (0 recompute au moment du run).

Sources agrégées (schémas réels vérifiés) :
  1. ~/jarvis-linux/BACKLOG_QUEUE.json  (liste de 400 tâches :
       id, bloc, bloc_nom, num, titre, priorite P0/P1/P2, effort_estime,
       statut todo/in_progress/done, lien_pipeline)
  2. ~/jarvis/jarvis_master.db table `tasks` (LIVE, LECTURE SEULE, mode=ro&immutable=1 :
       id, parent_id, title, context, status, progress, agent, machine, score)
  3. TODO_DYNAMIQUE.json (optionnel, ignoré proprement si absent)
  4. tâches ajoutées manuellement (--add) : source=manual, persistées dans la base dédiée.

Garde-fous :
  - jarvis_master.db ouverte UNIQUEMENT en lecture (file:...?mode=ro&immutable=1).
  - Aucune écriture dans les sources : tout l'état (statut, ajouts) vit dans la base overlay dédiée.
  - try/except partout, robuste aux schémas/fichiers manquants. Aucun root requis.

Commandes :
  --sync                             ré-agrège les sources → unified_plan.db (dédup par titre normalisé)
  --list [--priorite P0] [--statut todo] [--source X] [--tag Y] [--limit N]
  --next                             prochaine tâche todo (meilleur score/priorité) + contexte préchargé
  --show <uid>                       détail complet d'une tâche + contexte préchargé
  --done <uid>                       marque done (overlay dédié, jamais dans les sources)
  --add "<titre>" [--priorite P1]    ajoute une tâche manuelle (persistée)
  --stats                            répartition par source / priorité / statut
"""

import os
import re
import sys
import json
import time
import glob
import sqlite3
import argparse

HOME = os.path.expanduser("~")

# --- Chemins sources (surchargeable par env) --------------------------------
BACKLOG_JSON = os.environ.get(
    "JP_BACKLOG", os.path.join(HOME, "jarvis-linux", "BACKLOG_QUEUE.json")
)
MASTER_DB = os.environ.get(
    "JP_MASTER_DB", os.path.join(HOME, "jarvis", "jarvis_master.db")
)
DATA_DIR = os.path.join(HOME, "jarvis", "data")
UNIFIED_DB = os.environ.get("JP_UNIFIED_DB", os.path.join(DATA_DIR, "unified_plan.db"))
SKILLS_DIR = os.path.join(HOME, ".claude", "skills")
AGENTS_DIR = os.path.join(HOME, ".claude", "agents")

# Emplacements possibles pour un TODO_DYNAMIQUE.json (optionnel)
TODO_DYN_GLOBS = [
    os.path.join(HOME, "jarvis-linux", "contexte-maximal", "*", "TODO_DYNAMIQUE.json"),
    os.path.join(HOME, "jarvis", "TODO_DYNAMIQUE.json"),
    os.path.join(HOME, "jarvis-linux", "TODO_DYNAMIQUE.json"),
    os.path.join(HOME, "labo", "**", "TODO_DYNAMIQUE.json"),
]

PRIOS = ("P0", "P1", "P2")
PRIO_RANK = {"P0": 0, "P1": 1, "P2": 2}
# statut normalisé : actionnable d'abord
STATUT_RANK = {"todo": 0, "in_progress": 1, "analyzed": 2, "done": 3, "cancelled": 4}


# ============================================================================
#  Utilitaires
# ============================================================================
def _norm_titre(t):
    """Titre normalisé pour la déduplication."""
    try:
        t = (t or "").lower().strip()
        t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE)
        t = re.sub(r"\s+", " ", t).strip()
        return t[:200]
    except Exception:
        return (t or "")[:200]


def _norm_statut(raw, source):
    """Normalise les statuts hétérogènes vers todo/in_progress/analyzed/done/cancelled."""
    s = (raw or "").lower().strip()
    mapping = {
        "todo": "todo",
        "pending": "todo",
        "queued": "todo",
        "new": "todo",
        "open": "todo",
        "": "todo",
        "in_progress": "in_progress",
        "running": "in_progress",
        "active": "in_progress",
        "wip": "in_progress",
        "analyzed": "analyzed",
        "done": "done",
        "completed": "done",
        "complete": "done",
        "finished": "done",
        "ok": "done",
        "cancelled": "cancelled",
        "canceled": "cancelled",
        "skip": "cancelled",
        "failed": "cancelled",
    }
    return mapping.get(s, "todo")


def _norm_prio_from_score(score):
    """Master n'a pas de priorité → dérivée du score."""
    try:
        sc = float(score)
    except Exception:
        return "P2"
    if sc >= 2.0:
        return "P0"
    if sc >= 1.0:
        return "P1"
    return "P2"


def _load_skill_agent_sets():
    """Ensembles des skills/agents existants pour détecter le lien pipeline."""
    skills, agents = set(), set()
    try:
        for d in os.listdir(SKILLS_DIR):
            p = os.path.join(SKILLS_DIR, d)
            if os.path.isdir(p) and not d.startswith("_"):
                skills.add(d)
    except Exception:
        pass
    try:
        for f in os.listdir(AGENTS_DIR):
            if f.endswith(".md") and not f.startswith("_"):
                agents.add(f[:-3])
    except Exception:
        pass
    return skills, agents


def _detect_pipeline(lien, skills, agents):
    """Parse 'cat->cible1 / cible2 (note)' → détecte skills/agents/timers/scripts liés."""
    out = {
        "category": "",
        "skills": [],
        "agents": [],
        "timers": [],
        "scripts": [],
        "raw_targets": [],
    }
    try:
        lien = (lien or "").strip()
        if not lien:
            return out
        if "->" in lien:
            cat, rest = lien.split("->", 1)
            out["category"] = cat.strip()
        else:
            rest = lien
        for tok in rest.split("/"):
            tok = tok.strip()
            tok = re.sub(r"\(.*?\)", "", tok).strip()  # retire notes entre parenthèses
            if not tok or tok.lower() in ("none", "unassigned"):
                continue
            out["raw_targets"].append(tok)
            base = tok.split()[0] if tok else tok
            if base.endswith(".timer"):
                out["timers"].append(base)
            elif base.endswith(".py") or base.endswith(".sh"):
                out["scripts"].append(base)
            elif base in skills:
                out["skills"].append(base)
            elif base in agents:
                out["agents"].append(base)
            else:
                # heuristique nom : essaie de rattacher à un skill/agent connu
                if base in skills:
                    out["skills"].append(base)
                elif base in agents:
                    out["agents"].append(base)
                else:
                    out["raw_targets"][-1] = base  # garde le brut
    except Exception:
        pass
    return out


def _ready_cmd(detected, source, ref_id):
    """Commande prête à l'emploi déduite du contexte préchargé."""
    try:
        if detected.get("skills"):
            return "Skill: /%s" % detected["skills"][0]
        if detected.get("agents"):
            return "Agent: %s" % detected["agents"][0]
        if detected.get("scripts"):
            return "Script: %s" % detected["scripts"][0]
        if detected.get("timers"):
            return "systemctl start %s" % detected["timers"][0]
    except Exception:
        pass
    return ""


def _relevant_files(detected):
    """Fichiers pertinents préchargés (chemins skill/agent existants)."""
    files = []
    try:
        for sk in detected.get("skills", []):
            p = os.path.join(SKILLS_DIR, sk)
            if os.path.isdir(p):
                files.append(p)
        for ag in detected.get("agents", []):
            p = os.path.join(AGENTS_DIR, ag + ".md")
            if os.path.exists(p):
                files.append(p)
        for sc in detected.get("scripts", []):
            for cand in glob.glob(
                os.path.join(HOME, "jarvis*", "**", sc), recursive=True
            )[:1]:
                files.append(cand)
    except Exception:
        pass
    return files[:8]


# ============================================================================
#  Base overlay dédiée
# ============================================================================
def db_connect():
    """Ouvre (et crée) la base overlay DÉDIÉE en WAL."""
    os.makedirs(DATA_DIR, exist_ok=True)
    con = sqlite3.connect(UNIFIED_DB, timeout=30)
    try:
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
    except Exception:
        pass
    con.row_factory = sqlite3.Row
    _db_init(con)
    return con


def _db_init(con):
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS plan (
            uid        TEXT PRIMARY KEY,   -- source:ref_id
            source     TEXT,
            ref_id     TEXT,
            titre      TEXT,
            titre_norm TEXT,
            contexte   TEXT,
            priorite   TEXT,               -- P0/P1/P2 normalisée
            statut     TEXT,               -- todo/in_progress/analyzed/done/cancelled
            score      REAL,
            tags       TEXT,
            pipeline   TEXT,
            preloaded  TEXT,               -- JSON contexte prêt à l'emploi
            created_at TEXT,
            updated_at TEXT
        );
        CREATE INDEX IF NOT EXISTS ix_plan_norm   ON plan(titre_norm);
        CREATE INDEX IF NOT EXISTS ix_plan_statut ON plan(statut);
        CREATE INDEX IF NOT EXISTS ix_plan_prio   ON plan(priorite);
        CREATE INDEX IF NOT EXISTS ix_plan_source ON plan(source);

        -- overlay de statut : override PERSISTANT (survit aux --sync), jamais dans les sources
        CREATE TABLE IF NOT EXISTS status_overlay (
            uid        TEXT PRIMARY KEY,
            statut     TEXT,
            updated_at TEXT
        );

        -- tâches ajoutées manuellement (persistées, ré-agrégées à chaque sync)
        CREATE TABLE IF NOT EXISTS manual_tasks (
            ref_id     TEXT PRIMARY KEY,
            titre      TEXT,
            priorite   TEXT,
            statut     TEXT,
            contexte   TEXT,
            created_at TEXT
        );
        """
    )
    con.commit()


# ============================================================================
#  Lecteurs de sources (tous en LECTURE SEULE)
# ============================================================================
def read_backlog(skills, agents):
    rows = []
    try:
        if not os.path.exists(BACKLOG_JSON):
            return rows
        data = json.load(open(BACKLOG_JSON, encoding="utf-8"))
        items = (
            data
            if isinstance(data, list)
            else data.get("tasks", data.get("backlog", []))
        )
        for it in items:
            try:
                ref = str(it.get("id") or it.get("num") or len(rows))
                titre = (it.get("titre") or it.get("title") or "").strip()
                if not titre:
                    continue
                prio = (it.get("priorite") or "P2").upper()
                if prio not in PRIOS:
                    prio = "P2"
                lien = it.get("lien_pipeline", "")
                detected = _detect_pipeline(lien, skills, agents)
                tags = [
                    t
                    for t in [
                        it.get("bloc_nom"),
                        it.get("effort_estime"),
                        detected.get("category"),
                    ]
                    if t
                ]
                preloaded = {
                    "source": "backlog",
                    "ref_id": ref,
                    "titre": titre,
                    "bloc": it.get("bloc_nom"),
                    "effort": it.get("effort_estime"),
                    "pipeline_raw": lien,
                    "detected": detected,
                    "ready_cmd": _ready_cmd(detected, "backlog", ref),
                    "files": _relevant_files(detected),
                    "context_text": "%s | bloc=%s | effort=%s | pipeline=%s"
                    % (titre, it.get("bloc_nom"), it.get("effort_estime"), lien),
                }
                rows.append(
                    {
                        "uid": "backlog:%s" % ref,
                        "source": "backlog",
                        "ref_id": ref,
                        "titre": titre,
                        "contexte": preloaded["context_text"],
                        "priorite": prio,
                        "statut": _norm_statut(it.get("statut"), "backlog"),
                        "score": {"P0": 3.0, "P1": 2.0, "P2": 1.0}.get(prio, 1.0),
                        "tags": tags,
                        "pipeline": lien,
                        "preloaded": preloaded,
                    }
                )
            except Exception:
                continue
    except Exception as e:
        sys.stderr.write("[warn] backlog illisible: %s\n" % e)
    return rows


def read_master(skills, agents):
    """LECTURE SEULE stricte de jarvis_master.db (mode=ro&immutable=1)."""
    rows = []
    try:
        if not os.path.exists(MASTER_DB):
            return rows
        uri = "file:%s?mode=ro&immutable=1" % MASTER_DB
        con = sqlite3.connect(uri, uri=True, timeout=15)
        con.row_factory = sqlite3.Row
        try:
            cur = con.execute(
                "SELECT id,parent_id,title,context,status,progress,agent,machine,score "
                "FROM tasks"
            )
            for r in cur.fetchall():
                try:
                    titre = (r["title"] or "").strip()
                    if not titre:
                        continue
                    ref = str(r["id"])
                    prio = _norm_prio_from_score(r["score"])
                    ctx = r["context"] or ""
                    detected = {
                        "category": "",
                        "skills": [],
                        "agents": [],
                        "timers": [],
                        "scripts": [],
                        "raw_targets": [],
                    }
                    if r["agent"] and r["agent"] in agents:
                        detected["agents"].append(r["agent"])
                    tags = [t for t in [r["machine"], r["agent"]] if t]
                    preloaded = {
                        "source": "master",
                        "ref_id": ref,
                        "titre": titre,
                        "agent": r["agent"],
                        "machine": r["machine"],
                        "progress": r["progress"],
                        "parent_id": r["parent_id"],
                        "detected": detected,
                        "ready_cmd": _ready_cmd(detected, "master", ref),
                        "files": _relevant_files(detected),
                        "context_text": ctx or titre,
                    }
                    rows.append(
                        {
                            "uid": "master:%s" % ref,
                            "source": "master",
                            "ref_id": ref,
                            "titre": titre,
                            "contexte": ctx,
                            "priorite": prio,
                            "statut": _norm_statut(r["status"], "master"),
                            "score": float(r["score"])
                            if r["score"] is not None
                            else 1.0,
                            "tags": tags,
                            "pipeline": "",
                            "preloaded": preloaded,
                        }
                    )
                except Exception:
                    continue
        finally:
            con.close()
    except Exception as e:
        sys.stderr.write("[warn] master (ro) illisible: %s\n" % e)
    return rows


def read_todo_dyn(skills, agents):
    rows = []
    found = None
    try:
        for g in TODO_DYN_GLOBS:
            hits = sorted(glob.glob(g, recursive=True))
            if hits:
                found = hits[-1]
                break
        if not found:
            return rows
        data = json.load(open(found, encoding="utf-8"))
        items = (
            data
            if isinstance(data, list)
            else data.get("todos", data.get("tasks", data.get("items", [])))
        )
        if not isinstance(items, list):
            return rows
        for i, it in enumerate(items):
            try:
                if isinstance(it, str):
                    it = {"titre": it}
                titre = (
                    it.get("titre") or it.get("title") or it.get("task") or ""
                ).strip()
                if not titre:
                    continue
                ref = str(it.get("id") or i)
                prio = (it.get("priorite") or it.get("priority") or "P2").upper()
                if prio not in PRIOS:
                    prio = "P2"
                preloaded = {
                    "source": "todo_dyn",
                    "ref_id": ref,
                    "titre": titre,
                    "file": found,
                    "context_text": titre,
                    "detected": {},
                    "ready_cmd": "",
                    "files": [found],
                }
                rows.append(
                    {
                        "uid": "todo_dyn:%s" % ref,
                        "source": "todo_dyn",
                        "ref_id": ref,
                        "titre": titre,
                        "contexte": titre,
                        "priorite": prio,
                        "statut": _norm_statut(
                            it.get("statut") or it.get("status"), "todo_dyn"
                        ),
                        "score": {"P0": 3.0, "P1": 2.0, "P2": 1.0}.get(prio, 1.0),
                        "tags": ["todo_dyn"],
                        "pipeline": "",
                        "preloaded": preloaded,
                    }
                )
            except Exception:
                continue
    except Exception as e:
        sys.stderr.write("[warn] TODO_DYNAMIQUE ignoré: %s\n" % e)
    return rows


def read_manual(con):
    rows = []
    try:
        for r in con.execute("SELECT * FROM manual_tasks"):
            preloaded = {
                "source": "manual",
                "ref_id": r["ref_id"],
                "titre": r["titre"],
                "context_text": r["contexte"] or r["titre"],
                "detected": {},
                "ready_cmd": "",
                "files": [],
            }
            rows.append(
                {
                    "uid": "manual:%s" % r["ref_id"],
                    "source": "manual",
                    "ref_id": r["ref_id"],
                    "titre": r["titre"],
                    "contexte": r["contexte"] or "",
                    "priorite": r["priorite"] or "P2",
                    "statut": _norm_statut(r["statut"], "manual"),
                    "score": {"P0": 3.0, "P1": 2.0, "P2": 1.0}.get(
                        r["priorite"] or "P2", 1.0
                    ),
                    "tags": ["manual"],
                    "pipeline": "",
                    "preloaded": preloaded,
                }
            )
    except Exception:
        pass
    return rows


# ============================================================================
#  Agrégation / dédup
# ============================================================================
DOMINOS_DIR = os.environ.get(
    "JP_DOMINOS", os.path.join(HOME, "jarvis", "dominos-compiled", "dominos")
)
SERIES_DIR = os.environ.get(
    "JP_SERIES", os.path.join(HOME, "labo", "bibliotheque", "series")
)
CHRONO_JSON = os.environ.get(
    "JP_CHRONO", os.path.join(HOME, "jarvis", "data", "CHRONOLOGIE.json")
)
CHRONO_CAP = int(
    os.environ.get("JP_CHRONO_CAP", "100000")
)  # cap "démentiel" : tous les reports datés (dédup collapse les doublons)


def read_chronologie(skills, agents):
    """Reports datés (chronologie) → tâches 'lire/relire' préchargées, les CAP plus
    récentes. La chronologie complète reste dans CHRONOLOGIE.md."""
    rows = []
    try:
        if not os.path.exists(CHRONO_JSON):
            return rows
        data = json.load(open(CHRONO_JSON, encoding="utf-8"))
        data = [e for e in data if e.get("date", "0000-00-00") != "0000-00-00"]
        data.sort(key=lambda e: e.get("date", ""), reverse=True)  # + récents d'abord
        for i, e in enumerate(data[:CHRONO_CAP]):
            titre = (e.get("titre") or "").strip()
            path = e.get("path") or ""
            date = e.get("date") or ""
            if not titre:
                continue
            ref = "%s-%d" % (date, i)
            ready = "xdg-open '%s'" % path if path else ""
            preloaded = {
                "source": "report",
                "ref_id": ref,
                "titre": "Report %s: %s" % (date, titre),
                "date": date,
                "ready_cmd": ready,
                "files": [path] if path else [],
                "context_text": "Report daté %s — %s. Ouvrir: %s"
                % (date, titre, ready),
            }
            rows.append(
                {
                    "uid": "report:%s" % ref,
                    "source": "report",
                    "ref_id": ref,
                    "titre": "Report %s: %s" % (date, titre),
                    "contexte": preloaded["context_text"],
                    "priorite": "P2",
                    "statut": "todo",
                    "score": 1.0,
                    "tags": ["report", date],
                    "pipeline": "",
                    "preloaded": preloaded,
                }
            )
    except Exception as e:
        sys.stderr.write("[warn] chronologie illisible: %s\n" % e)
    return rows


def read_dominos(skills, agents):
    """Chaque domino compilé = une tâche actionnable (ready_cmd = `dominos <slug>`)."""
    rows = []
    try:
        if not os.path.isdir(DOMINOS_DIR):
            return rows
        for fn in sorted(os.listdir(DOMINOS_DIR)):
            if not fn.endswith(".sh"):
                continue
            slug = fn[:-3]
            path = os.path.join(DOMINOS_DIR, fn)
            titre, danger, nsteps = slug, "🟢", 0
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    txt = fh.read()
                m = re.search(r"^# domino:\s*(.+)$", txt, re.M)
                if m:
                    titre = m.group(1).strip()
                nsteps = len(re.findall(r'^step "', txt, re.M))
                if re.search(r'^step ".*" "\U0001f534"', txt, re.M):
                    danger = "🔴"
                elif re.search(r'^step ".*" "\U0001f7e0"', txt, re.M):
                    danger = "🟠"
            except Exception:
                pass
            preloaded = {
                "source": "domino",
                "ref_id": slug,
                "titre": "Domino: %s" % titre,
                "danger": danger,
                "steps": nsteps,
                "ready_cmd": "dominos %s" % slug,
                "run_cmd": "dominos %s --run" % slug,
                "files": [path],
                "context_text": "Domino « %s » — %d steps, danger %s. Aperçu: `dominos %s` · Exécuter: `dominos %s --run`"
                % (titre, nsteps, danger, slug, slug),
            }
            rows.append(
                {
                    "uid": "domino:%s" % slug,
                    "source": "domino",
                    "ref_id": slug,
                    "titre": "Domino: %s" % titre,
                    "contexte": preloaded["context_text"],
                    "priorite": "P2",
                    "statut": "todo",
                    "score": 1.0,
                    "tags": ["domino", danger],
                    "pipeline": "",
                    "preloaded": preloaded,
                }
            )
    except Exception as e:
        sys.stderr.write("[warn] dominos illisible: %s\n" % e)
    # Séries biblio (scripts prêts) — aussi lançables via `dominos <slug>`
    try:
        if os.path.isdir(SERIES_DIR):
            for fn in sorted(os.listdir(SERIES_DIR)):
                if not fn.endswith(".sh"):
                    continue
                slug = fn[:-3]
                path = os.path.join(SERIES_DIR, fn)
                preloaded = {
                    "source": "domino",
                    "ref_id": "serie:%s" % slug,
                    "titre": "Série: %s" % slug,
                    "danger": "🟠",
                    "ready_cmd": "dominos %s" % slug,
                    "run_cmd": "dominos %s --run" % slug,
                    "files": [path],
                    "context_text": "Série biblio « %s » (script prêt). Aperçu: `dominos %s` · Exécuter: `dominos %s --run`"
                    % (slug, slug, slug),
                }
                rows.append(
                    {
                        "uid": "serie:%s" % slug,
                        "source": "domino",
                        "ref_id": "serie:%s" % slug,
                        "titre": "Série: %s" % slug,
                        "contexte": preloaded["context_text"],
                        "priorite": "P2",
                        "statut": "todo",
                        "score": 1.0,
                        "tags": ["domino", "serie", "🟠"],
                        "pipeline": "",
                        "preloaded": preloaded,
                    }
                )
    except Exception as e:
        sys.stderr.write("[warn] séries illisibles: %s\n" % e)
    return rows


def cmd_sync(con):
    t0 = time.time()
    skills, agents = _load_skill_agent_sets()
    per_source = {}
    allrows = []
    for reader, name in (
        (read_backlog, "backlog"),
        (read_master, "master"),
        (read_todo_dyn, "todo_dyn"),
        (read_dominos, "domino"),
        (read_chronologie, "report"),
    ):
        rows = reader(skills, agents)
        per_source[name] = len(rows)
        allrows.extend(rows)
    manual = read_manual(con)
    per_source["manual"] = len(manual)
    allrows.extend(manual)

    total_raw = len(allrows)

    # Overlays de statut existants (persistent à travers les syncs)
    overlay = {}
    try:
        for r in con.execute("SELECT uid,statut FROM status_overlay"):
            overlay[r["uid"]] = r["statut"]
    except Exception:
        pass

    # Dédup par titre normalisé : garde le meilleur (statut actionnable puis priorité puis score)
    best = {}
    dup = 0
    for row in allrows:
        key = _norm_titre(row["titre"])
        if not key:
            key = row["uid"]
        cand = row
        if key in best:
            dup += 1
            cur = best[key]

            # préfère actionnable (statut rank bas), puis priorité, puis score
            def rankof(x):
                return (
                    STATUT_RANK.get(x["statut"], 9),
                    PRIO_RANK.get(x["priorite"], 9),
                    -float(x["score"] or 0),
                )

            if rankof(cand) < rankof(cur):
                # fusionne tags/pipeline dans le gagnant
                cand["tags"] = sorted(
                    set((cand.get("tags") or []) + (cur.get("tags") or []))
                )
                best[key] = cand
            else:
                cur["tags"] = sorted(
                    set((cur.get("tags") or []) + (cand.get("tags") or []))
                )
        else:
            best[key] = cand

    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    # Reconstruit la table plan
    con.execute("DELETE FROM plan;")
    ins = 0
    for row in best.values():
        try:
            statut = overlay.get(row["uid"], row["statut"])  # overlay prioritaire
            con.execute(
                "INSERT OR REPLACE INTO plan "
                "(uid,source,ref_id,titre,titre_norm,contexte,priorite,statut,score,tags,pipeline,preloaded,created_at,updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    row["uid"],
                    row["source"],
                    row["ref_id"],
                    row["titre"],
                    _norm_titre(row["titre"]),
                    row["contexte"],
                    row["priorite"],
                    statut,
                    float(row["score"] or 0),
                    json.dumps(row.get("tags") or [], ensure_ascii=False),
                    row.get("pipeline") or "",
                    json.dumps(row.get("preloaded") or {}, ensure_ascii=False),
                    now,
                    now,
                ),
            )
            ins += 1
        except Exception:
            continue
    con.commit()

    dt = time.time() - t0
    print("=== jarvis-plan --sync ===")
    print("Base overlay dédiée : %s" % UNIFIED_DB)
    print("-" * 52)
    for name in ("backlog", "master", "todo_dyn", "manual"):
        print("  %-10s : %5d tâches" % (name, per_source.get(name, 0)))
    print("-" * 52)
    print("  Total brut agrégé : %5d" % total_raw)
    print("  Doublons fusionnés: %5d (dédup titre normalisé)" % dup)
    print("  Total UNIFIÉ      : %5d tâches" % ins)
    print("  Overlays statut   : %5d préservés" % len(overlay))
    print("  Durée            : %.2fs" % dt)
    return 0


# ============================================================================
#  Affichage / requêtes
# ============================================================================
def _row_ok_or_hint(con):
    try:
        n = con.execute("SELECT count(*) c FROM plan").fetchone()["c"]
        if n == 0:
            print("[info] plan vide → lance d'abord : jarvis-plan --sync")
            return False
        return True
    except Exception:
        print("[info] lance d'abord : jarvis-plan --sync")
        return False


def cmd_list(con, args):
    if not _row_ok_or_hint(con):
        return 1
    q = "SELECT uid,source,titre,priorite,statut,score FROM plan WHERE 1=1"
    p = []
    if args.priorite:
        q += " AND priorite=?"
        p.append(args.priorite.upper())
    if args.statut:
        q += " AND statut=?"
        p.append(args.statut.lower())
    if args.source:
        q += " AND source=?"
        p.append(args.source.lower())
    if args.tag:
        q += " AND tags LIKE ?"
        p.append("%" + args.tag + "%")
    q += " ORDER BY (priorite='P0') DESC, priorite ASC, score DESC LIMIT ?"
    p.append(int(args.limit or 30))
    rows = con.execute(q, p).fetchall()
    print("=== jarvis-plan --list (%d) ===" % len(rows))
    print("%-14s %-9s %-4s %-12s %s" % ("UID", "SOURCE", "PRIO", "STATUT", "TITRE"))
    print("-" * 100)
    for r in rows:
        print(
            "%-14s %-9s %-4s %-12s %s"
            % (
                r["uid"],
                r["source"],
                r["priorite"],
                r["statut"],
                (r["titre"] or "")[:58],
            )
        )
    return 0


def _print_preloaded(r):
    try:
        pl = json.loads(r["preloaded"] or "{}")
    except Exception:
        pl = {}
    print("  contexte préchargé :")
    print("    texte    : %s" % (pl.get("context_text") or r["contexte"] or "")[:220])
    det = pl.get("detected") or {}
    if any(det.get(k) for k in ("skills", "agents", "timers", "scripts")):
        print("    skills   : %s" % (", ".join(det.get("skills", [])) or "-"))
        print("    agents   : %s" % (", ".join(det.get("agents", [])) or "-"))
        print("    timers   : %s" % (", ".join(det.get("timers", [])) or "-"))
        print("    scripts  : %s" % (", ".join(det.get("scripts", [])) or "-"))
    if pl.get("ready_cmd"):
        print("    >> PRÊT  : %s" % pl["ready_cmd"])
    if pl.get("files"):
        print("    fichiers : %s" % ", ".join(pl["files"]))
    if pl.get("agent") or pl.get("machine"):
        print(
            "    exec     : agent=%s machine=%s progress=%s"
            % (pl.get("agent"), pl.get("machine"), pl.get("progress"))
        )


def cmd_next(con):
    if not _row_ok_or_hint(con):
        return 1
    r = con.execute(
        "SELECT * FROM plan WHERE statut IN ('todo','in_progress') "
        "ORDER BY (statut='in_progress') DESC, priorite ASC, score DESC, uid ASC LIMIT 1"
    ).fetchone()
    if not r:
        print("[ok] aucune tâche todo/in_progress restante.")
        return 0
    print("=== jarvis-plan --next ===")
    print("UID      : %s" % r["uid"])
    print("Titre    : %s" % r["titre"])
    print(
        "Source   : %s   Priorité : %s   Statut : %s   Score : %.2f"
        % (r["source"], r["priorite"], r["statut"], r["score"] or 0)
    )
    if r["pipeline"]:
        print("Pipeline : %s" % r["pipeline"])
    _print_preloaded(r)
    print("-" * 52)
    print("→ jarvis-plan --done %s   (marque terminé, overlay dédié)" % r["uid"])
    return 0


def cmd_show(con, uid):
    r = con.execute("SELECT * FROM plan WHERE uid=?", (uid,)).fetchone()
    if not r:
        print("[warn] uid introuvable: %s" % uid)
        return 1
    print("=== jarvis-plan --show %s ===" % uid)
    for k in (
        "uid",
        "source",
        "ref_id",
        "titre",
        "priorite",
        "statut",
        "score",
        "tags",
        "pipeline",
    ):
        print("%-9s: %s" % (k, r[k]))
    _print_preloaded(r)
    return 0


def cmd_done(con, uid):
    r = con.execute("SELECT uid FROM plan WHERE uid=?", (uid,)).fetchone()
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    if not r:
        print(
            "[warn] uid introuvable dans le plan: %s (overlay enregistré quand même)"
            % uid
        )
    con.execute(
        "INSERT OR REPLACE INTO status_overlay(uid,statut,updated_at) VALUES (?,?,?)",
        (uid, "done", now),
    )
    con.execute("UPDATE plan SET statut='done', updated_at=? WHERE uid=?", (now, uid))
    # si tâche manuelle, maj aussi la table manual_tasks
    if uid.startswith("manual:"):
        con.execute(
            "UPDATE manual_tasks SET statut='done' WHERE ref_id=?",
            (uid.split(":", 1)[1],),
        )
    con.commit()
    print("[ok] %s → done (overlay dédié, sources live intactes)" % uid)
    return 0


def cmd_add(con, titre, priorite):
    titre = (titre or "").strip()
    if not titre:
        print("[warn] titre vide")
        return 1
    prio = (priorite or "P2").upper()
    if prio not in PRIOS:
        prio = "P2"
    ref = "m%d" % int(time.time())
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    con.execute(
        "INSERT OR REPLACE INTO manual_tasks(ref_id,titre,priorite,statut,contexte,created_at) "
        "VALUES (?,?,?,?,?,?)",
        (ref, titre, prio, "todo", titre, now),
    )
    uid = "manual:%s" % ref
    pl = {
        "source": "manual",
        "ref_id": ref,
        "titre": titre,
        "context_text": titre,
        "detected": {},
        "ready_cmd": "",
        "files": [],
    }
    con.execute(
        "INSERT OR REPLACE INTO plan "
        "(uid,source,ref_id,titre,titre_norm,contexte,priorite,statut,score,tags,pipeline,preloaded,created_at,updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            uid,
            "manual",
            ref,
            titre,
            _norm_titre(titre),
            titre,
            prio,
            "todo",
            {"P0": 3.0, "P1": 2.0, "P2": 1.0}[prio],
            json.dumps(["manual"]),
            "",
            json.dumps(pl, ensure_ascii=False),
            now,
            now,
        ),
    )
    con.commit()
    print("[ok] ajouté %s [%s] : %s" % (uid, prio, titre))
    return 0


def cmd_stats(con):
    if not _row_ok_or_hint(con):
        return 1
    print("=== jarvis-plan --stats ===")
    tot = con.execute("SELECT count(*) c FROM plan").fetchone()["c"]
    print("Total unifié : %d tâches" % tot)
    for dim, label in (
        ("source", "Par source"),
        ("priorite", "Par priorité"),
        ("statut", "Par statut"),
    ):
        print("\n%s :" % label)
        for r in con.execute(
            "SELECT %s k, count(*) c FROM plan GROUP BY %s ORDER BY c DESC" % (dim, dim)
        ):
            print("  %-14s : %5d" % (r["k"], r["c"]))
    # todo actionnable par priorité
    print("\nActionnable (todo+in_progress) par priorité :")
    for r in con.execute(
        "SELECT priorite k, count(*) c FROM plan "
        "WHERE statut IN ('todo','in_progress') GROUP BY priorite ORDER BY priorite"
    ):
        print("  %-14s : %5d" % (r["k"], r["c"]))
    return 0


# ============================================================================
#  CLI
# ============================================================================
_DOMINOS_BIN = os.path.join(HOME, "jarvis", "bin", "dominos")
_SAFE_VERBS = {
    "git": {"status", "log", "diff", "branch", "remote"},
    "systemctl": {"is-active", "status", "list-units", "list-timers", "show", "cat"},
    "journalctl": None,
    "ls": None,
    "cat": None,
    "stat": None,
    "df": None,
    "free": None,
    "uptime": None,
    "nvidia-smi": None,
    "date": None,
    "whoami": None,
    "hostname": None,
    "echo": None,
}
_META = set("$`|;&<>(){}*?!\\\n")


def _safe_argv(cmd):
    """Renvoie ('domino'|'ro', argv) si la commande est SÛRE (read-only, sans shell),
    sinon None. Jamais de bash -c : refuse tout métacaractère shell."""
    if not cmd or any(ch in cmd for ch in _META):
        return None
    import shlex

    try:
        parts = shlex.split(cmd)
    except Exception:
        return None
    if not parts:
        return None
    v = parts[0]
    if v == "dominos":
        return ("domino", parts)
    if v in _SAFE_VERBS:
        sub = _SAFE_VERBS[v]
        if sub is None or (len(parts) > 1 and parts[1] in sub):
            return ("ro", parts)
    return None


def cmd_do(con, n):
    """EXÉCUTE réellement N tâches SÛRES du plan et avance l'overlay (todo→done/analyzed).
    dominos → dry-run (analyzed) · commandes read-only validées → done · risqué → laissé todo."""
    import subprocess

    # Priorise les tâches RÉELLEMENT auto-doables (dominos = ready_cmd sûr) puis
    # la priorité. Sinon les P0 non-auto en tête feraient tout sauter.
    rows = con.execute(
        "SELECT uid, priorite, preloaded FROM plan WHERE statut IN ('todo','in_progress') "
        "ORDER BY (source='domino') DESC, "
        "CASE priorite WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 ELSE 2 END, score DESC "
        "LIMIT ?",
        (max(n * 8, 200),),
    ).fetchall()
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    rdir = os.path.join(HOME, "jarvis", "data", "task_results")
    os.makedirs(rdir, exist_ok=True)
    processed = done = analyzed = skipped = 0
    for uid, prio, pre in rows:
        if processed >= n:
            break
        try:
            cmd = (json.loads(pre or "{}")).get("ready_cmd", "")
        except Exception:
            cmd = ""
        if not cmd:
            continue
        cls = _safe_argv(cmd)
        if cls is None:
            skipped += 1
            continue
        kind, parts = cls
        try:
            if kind == "domino":
                slug = parts[1] if len(parts) > 1 else ""
                if not re.match(r"^[\w.-]+$", slug):
                    skipped += 1
                    continue
                # DRY-RUN uniquement : l'exécution réelle auto n'est PAS fiable (même un
                # domino "🟢" peut bloquer). Aperçu sûr, stdin coupé → statut 'analyzed'.
                out = subprocess.run(
                    [_DOMINOS_BIN, slug],
                    capture_output=True,
                    text=True,
                    timeout=25,
                    stdin=subprocess.DEVNULL,
                )
                status = "analyzed"
            else:
                out = subprocess.run(parts, capture_output=True, text=True, timeout=20)
                status = "done"
            txt = ((out.stdout or "") + (out.stderr or ""))[:2500]
        except Exception:
            skipped += 1
            continue
        try:
            fn = uid.replace("/", "_").replace(":", "_") + ".md"
            with open(os.path.join(rdir, fn), "w", encoding="utf-8") as fh:
                fh.write(
                    "# %s\nstatut: %s\ncmd: %s\nts: %s\n\n%s\n"
                    % (uid, status, cmd, now, txt)
                )
        except Exception:
            pass
        con.execute(
            "INSERT OR REPLACE INTO status_overlay(uid,statut,updated_at) VALUES (?,?,?)",
            (uid, status, now),
        )
        con.execute(
            "UPDATE plan SET statut=?,updated_at=? WHERE uid=?", (status, now, uid)
        )
        processed += 1
        done += status == "done"
        analyzed += status == "analyzed"
    con.commit()
    print("=== jarvis-plan --do %d ===" % n)
    print(
        "Traité : %d (✅ done %d · 🔎 analyzed %d) · sautés (risqué/non-auto) : %d"
        % (processed, done, analyzed, skipped)
    )
    print("Résultats : %s" % rdir)


def main():
    ap = argparse.ArgumentParser(
        prog="jarvis-plan",
        description="Planning unifié JARVIS (todolist dynamique + préchargement)",
    )
    ap.add_argument(
        "--sync", action="store_true", help="ré-agrège les sources → unified_plan.db"
    )
    ap.add_argument("--list", action="store_true", help="liste filtrable")
    ap.add_argument(
        "--next", action="store_true", help="prochaine tâche + contexte préchargé"
    )
    ap.add_argument("--show", metavar="UID", help="détail d'une tâche")
    ap.add_argument("--done", metavar="UID", help="marque done (overlay dédié)")
    ap.add_argument(
        "--do",
        type=int,
        metavar="N",
        default=0,
        help="EXÉCUTE N tâches sûres du plan et avance l'overlay (dominos dry-run + read-only)",
    )
    ap.add_argument("--add", metavar="TITRE", help="ajoute une tâche manuelle")
    ap.add_argument(
        "--stats", action="store_true", help="répartition par source/priorité/statut"
    )
    ap.add_argument("--priorite", help="filtre P0/P1/P2 (list) ou priorité (add)")
    ap.add_argument("--statut", help="filtre statut (list)")
    ap.add_argument("--source", help="filtre source (list)")
    ap.add_argument("--tag", help="filtre tag (list)")
    ap.add_argument("--limit", type=int, default=30, help="limite (list)")
    args = ap.parse_args()

    try:
        con = db_connect()
    except Exception as e:
        sys.stderr.write("[fatal] base overlay inaccessible: %s\n" % e)
        return 2

    try:
        if args.sync:
            return cmd_sync(con)
        if args.add:
            return cmd_add(con, args.add, args.priorite)
        if args.done:
            return cmd_done(con, args.done)
        if args.do:
            return cmd_do(con, args.do)
        if args.show:
            return cmd_show(con, args.show)
        if args.next:
            return cmd_next(con)
        if args.stats:
            return cmd_stats(con)
        if args.list:
            return cmd_list(con, args)
        ap.print_help()
        return 0
    except Exception as e:
        sys.stderr.write("[erreur] %s\n" % e)
        return 1
    finally:
        try:
            con.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
