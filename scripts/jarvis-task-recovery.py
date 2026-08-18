#!/usr/bin/env python3
"""jarvis-task-recovery.py — robustesse production (E1) : recovery des tâches bloquées.

Sans ça, les tâches `running` restent stuck indéfiniment et les `error` ne sont jamais
retentées. Ce script (branché sur un timer 5min existant) :
  - running > STUCK_MIN minutes  → remis `pending` (l'exécuteur les reprend)
  - error : retry compté dans le contexte  → `pending` si retries < MAX_RETRY,
            sinon `to_validate` (nécessite un œil humain, pas une boucle infinie)

Statut `to_validate` = nouvel état pour les tâches outward/risquées/échouées-max.
Idempotent, logs structurés, --dry par défaut, --go pour agir. 0-token.
"""

from __future__ import annotations

import os
import re
import sqlite3
import sys
import time

DB = os.path.expanduser("~/jarvis/jarvis_master.db")
LOG = os.path.expanduser("~/jarvis/logs/task-recovery.log")
STUCK_MIN = 30
MAX_RETRY = 2


def log(msg):
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(
                f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}][RECOVERY] {msg}\n"
            )
    except Exception:
        pass


def main() -> int:
    go = "--go" in sys.argv
    # WAL : un seul écrivain à la fois, et plusieurs producteurs permanents
    # écrivent en continu — 15 s ne suffisaient pas, d'où "database is locked".
    c = sqlite3.connect(DB, timeout=120)
    c.execute("PRAGMA busy_timeout=120000")

    # 1) running stuck > 30min → pending
    stuck = c.execute(
        "SELECT id FROM tasks WHERE status='running' "
        "AND updated_at < datetime('now', ?)",
        (f"-{STUCK_MIN} minutes",),
    ).fetchall()
    # 2) error → retry compté (dans context) → pending ou to_validate
    errs = c.execute(
        "SELECT id, COALESCE(context,'') FROM tasks WHERE status='error'"
    ).fetchall()

    to_pending, to_validate = list(stuck), []
    err_actions = []
    for tid, ctx in errs:
        m = re.search(r"retry=(\d+)", ctx)
        n = int(m.group(1)) + 1 if m else 1
        newctx = (
            re.sub(r"retry=\d+", f"retry={n}", ctx) if m else (ctx + f" · retry={n}")
        )
        if n <= MAX_RETRY:
            err_actions.append((tid, "pending", newctx))
        else:
            err_actions.append((tid, "to_validate", newctx))
            to_validate.append(tid)

    msg = (
        f"stuck→pending={len(stuck)} · error→retry={sum(1 for _, s, _ in err_actions if s == 'pending')} "
        f"· error→to_validate={len(to_validate)}"
    )
    if not go:
        print(f"[recovery] DRY : {msg}")
        c.close()
        return 0

    now = "CURRENT_TIMESTAMP"
    for (tid,) in stuck:
        c.execute(
            f"UPDATE tasks SET status='pending', updated_at={now} WHERE id=?", (tid,)
        )
    for tid, st, newctx in err_actions:
        c.execute(
            f"UPDATE tasks SET status=?, context=?, updated_at={now} WHERE id=?",
            (st, newctx[:500], tid),
        )
    c.commit()
    c.close()
    print(f"[recovery] GO : {msg}")
    log(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
