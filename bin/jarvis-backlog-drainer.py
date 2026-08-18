#!/usr/bin/env python3
"""jarvis-backlog-drainer.py — PONT overlay → file exécutable.

Cause du blocage : l'overlay `unified_plan.db` (7000+ tâches todo) n'est jamais lu
par l'exécuteur, qui ne consomme que `jarvis_master.db.tasks WHERE pending`.
Ce drainer pulle les tâches todo PRIORISÉES de l'overlay, dédup, et les insère
dans jarvis_master (pending) → l'exécuteur (routage source + exécution réelle +
prod-exec) les traite. La boucle est fermée par jarvis-backlog-reconcile.py.

Priorité : plani → EXÉCUTE. Cap par cycle (anti-flood/OOM). 0-token.
Usage : jarvis-backlog-drainer.py [--priorite P0|P1|P2] [--limit N] [--dry|--go]
"""

from __future__ import annotations

import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

OVERLAY = os.path.expanduser("~/jarvis/data/unified_plan.db")
MASTER = os.path.expanduser("~/jarvis/jarvis_master.db")
LOG = os.path.expanduser("~/jarvis/logs/backlog-drainer.log")
CAP = 25  # défaut anti-flood


def log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"[{ts}][DRAIN] {msg}\n")
    except Exception:
        pass


def _arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


SETPOINT = 100  # file pending cible (le « bon rythme »)
MAX_CAP = 200


def _adaptive_cap(master_db) -> int:
    """RYTHME ADAPTATIF : draine pour maintenir la file pending ~SETPOINT.
    File pleine (exécuteurs en retard) → draine peu/rien ; file basse → draine plus.
    Contrôleur proportionnel simple = converge vers le bon débit (apprentissage)."""
    try:
        c = sqlite3.connect(f"file:{master_db}?mode=ro", uri=True)
        pending = c.execute(
            "SELECT count(*) FROM tasks WHERE status='pending'"
        ).fetchone()[0]
        c.close()
    except Exception:
        pending = 0
    return max(0, min(MAX_CAP, SETPOINT - pending)), pending


def main() -> int:
    go = "--go" in sys.argv
    prio = _arg("--priorite")  # None = P0 puis P1 puis P2
    if "--limit" in sys.argv:
        limit = int(_arg("--limit", str(CAP)))
        cur_pending = None
    else:
        # défaut = ADAPTATIF (auto-régulé selon la file)
        limit, cur_pending = _adaptive_cap(MASTER)
        log(f"adaptatif: pending={cur_pending} setpoint={SETPOINT} → cap={limit}")

    # statut effectif = override status_overlay sinon plan.statut ; on veut 'todo'
    ov = sqlite3.connect(f"file:{OVERLAY}?mode=ro", uri=True)
    ov.row_factory = sqlite3.Row
    order = "CASE priorite WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 ELSE 2 END, score DESC"
    where = "COALESCE((SELECT statut FROM status_overlay o WHERE o.uid=p.uid), p.statut)='todo'"
    if prio:
        where += f" AND p.priorite='{prio}'"
    rows = ov.execute(
        f"SELECT uid, titre, priorite FROM plan p WHERE {where} "
        f"ORDER BY {order} LIMIT ?",
        (limit * 3,),  # marge pour la dédup
    ).fetchall()
    ov.close()

    m = sqlite3.connect(MASTER, timeout=15)
    m.execute("PRAGMA busy_timeout=15000")
    # dédup : titres déjà en jarvis_master (pending OU done récent) + uid déjà drainé
    seen_titles = {
        r[0]
        for r in m.execute(
            "SELECT title FROM tasks WHERE status='pending' "
            "OR (status='done' AND updated_at > datetime('now','-2 day'))"
        )
    }
    seen_uids = {
        r[0]
        for r in m.execute(
            "SELECT substr(context, instr(context,'uid=')+4, 40) FROM tasks "
            "WHERE context LIKE '%uid=%'"
        )
        if r[0]
    }

    inserted = 0
    by_prio = {}
    for r in rows:
        if inserted >= limit:
            break
        uid, titre, p = r["uid"], (r["titre"] or "").strip(), r["priorite"] or "P2"
        if not titre or titre in seen_titles or uid in seen_uids:
            continue
        # nettoie le titre (les report ont des préfixes [date·sujet]** )
        clean = re.sub(r"^\[[^\]]+\]\s*\**", "", titre).strip() or titre
        seen_titles.add(titre)
        seen_uids.add(uid)
        ctx = f"🔵 [drained] uid={uid} prio={p}"
        title = clean[:180]
        if go:
            m.execute(
                "INSERT INTO tasks(title, context, status, machine) "
                "VALUES(?,?,'pending','M1')",
                (title, ctx),
            )
            # mapping robuste uid↔titre (reconcile matche par titre, quel que soit
            # le consommateur qui traite la tâche → survit à la concurrence)
            _MAP = os.path.expanduser("~/jarvis/data/.drained_map.tsv")
            with open(_MAP, "a", encoding="utf-8") as mf:
                mf.write(f"{uid}\t{title}\n")
        inserted += 1
        by_prio[p] = by_prio.get(p, 0) + 1

    if go:
        m.commit()
    pending = m.execute("SELECT count(*) FROM tasks WHERE status='pending'").fetchone()[
        0
    ]
    m.close()

    tag = "GO" if go else "DRY"
    msg = f"{tag} +{inserted} tâches drainées {dict(by_prio)} · file pending={pending}"
    print(f"[drainer] {msg}")
    log(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
