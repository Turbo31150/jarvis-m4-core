"""Watchdog — détecte les workers silencieux et les jobs orphelins.

Ne tue jamais aveuglément : identifier → vérifier → annuler proprement →
sauvegarder → relancer → revérifier. Backoff, pas de boucle infinie.
"""

from __future__ import annotations

import time

from . import checkpoint as cp
from . import config as cfgmod
from .journal import Journal

WAITING_STATES = (
    "WAITING_FOR_MODEL",
    "WAITING_FOR_TOKEN",
    "WAITING_FOR_WORKER",
    "WAITING_FOR_QUEUE",
    "RECOVERING",
)


def inspect_workers(dispatcher) -> list[dict]:
    """Classe chaque worker d'après son heartbeat réel."""
    idle_limit = float(dispatcher.cfg.get("timeouts", {}).get("idle", 30.0))
    out = []
    for w in dispatcher.workers.values():
        hb = w.hb
        verdict = hb.status
        if hb.status == "RUNNING" and hb.age_s() > idle_limit:
            verdict = "TIMEOUT"
        out.append({**hb.to_dict(), "verdict": verdict, "idle_limit_s": idle_limit})
    return out


def sweep(max_age_s: float = 600.0, act: bool = False) -> dict:
    """Balaye les jobs figés. `act=False` = diagnostic seul (par défaut)."""
    stale = cp.stale_jobs(max_age_s)
    actions = []
    for j in stale:
        jid = j["job_id"]
        jour = Journal(jid)
        store = cp.JobStore(jid)
        pending = store.pending_tasks()
        detail = {
            "job_id": jid,
            "status": j["status"],
            "pending": len(pending),
            "age_s": round(time.time() - j["mtime"]),
        }
        jour.emit("WATCHDOG", reason="job figé", **detail)
        if act:
            # Action conservatrice : on marque RECOVERABLE, on ne détruit rien.
            store.set_status("RECOVERABLE")
            jour.emit("RECOVERY", action="marqué RECOVERABLE, reprenable via `resume`")
            detail["action"] = "RECOVERABLE"
        else:
            detail["action"] = "diagnostic seul (utiliser --act pour marquer)"
        actions.append(detail)
    return {"checked_dir": str(cfgmod.JOB_DIR), "stale": len(stale), "actions": actions}


def render(report: dict) -> str:
    if not report["stale"]:
        return f"WATCHDOG: aucun job figé ({report['checked_dir']})"
    lines = [f"WATCHDOG: {report['stale']} job(s) figé(s)"]
    for a in report["actions"]:
        lines.append(
            f"  {a['job_id']}  status={a['status']} pending={a['pending']} "
            f"age={a['age_s']}s → {a['action']}"
        )
    return "\n".join(lines)
