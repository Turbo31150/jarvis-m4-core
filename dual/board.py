"""Board — vue d'état alimentée automatiquement par le journal et les checkpoints.

Aucune saisie manuelle : tout vient de logs/dual/*.jsonl et data/dual-jobs/*.json.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from . import checkpoint as cp
from . import config as cfgmod
from .journal import Journal

W = 64


def _line(left="", right=""):
    pad = W - 4 - len(left) - len(right)
    return f"│ {left}{' ' * max(pad, 1)}{right} │"


def _sep(ch="─"):
    return "├" + ch * (W - 2) + "┤"


def snapshot(probe: bool = True) -> dict:
    cfg = cfgmod.resolve(force_discover=probe)
    jobs = cp.list_jobs()
    active = [j for j in jobs if j["status"] in ("RUNNING", "PENDING")]
    last = jobs[0] if jobs else None
    events = Journal(last["job_id"]).read() if last else []
    errors = [e for e in events if e["event"] in ("WORKER_FAILED", "RETRY")]
    return {
        "cfg": cfg,
        "jobs": jobs,
        "active": active,
        "last": last,
        "events": events,
        "errors": errors,
    }


def render(probe: bool = True) -> str:
    s = snapshot(probe)
    cfg, last = s["cfg"], s["last"]
    out = [
        "┌" + "─" * (W - 2) + "┐",
        _line(
            "JARVIS DUAL ORCHESTRATOR", datetime.now(timezone.utc).strftime("%H:%M:%SZ")
        ),
        _sep(),
    ]

    provs = cfg.get("providers", {})
    out.append(_line("MASTER", "● HEALTHY" if provs else "● DEGRADED"))
    for alias, p in provs.items():
        out.append(_line(f"  {alias}", f"● UP  {len(p['models'])} modèles"))
    if not provs:
        out.append(_line("  providers", "● AUCUN BACKEND"))

    for slot, spec in cfg.get("workers", {}).items():
        out.append(_line(f"  {slot} {spec['model'][:24]}", f"◐ {spec['provider']}"))
    if len(cfg.get("workers", {})) < 2:
        out.append(_line("  DUAL", "⚠ MODE DÉGRADÉ (1 worker)"))

    out.append(_sep())
    if last:
        st = last["status"]
        out.append(_line(f"JOB {last['job_id'][-18:]}", st))
        out.append(_line(f"  mode={last['mode']}", f"étapes {last['progress']}"))
        done, total = (int(x) for x in last["progress"].split("/"))
        bar_n = int((done / total) * 20) if total else 0
        out.append(
            _line(
                "  " + "█" * bar_n + "░" * (20 - bar_n),
                f"{(done / total * 100 if total else 0):.0f}%",
            )
        )
        for ev in s["events"][-3:]:
            out.append(_line(f"  {ev['event'][:22]}", str(ev.get("worker") or "")[:16]))
    else:
        out.append(_line("JOB", "aucun job enregistré"))

    out.append(_sep())
    out.append(
        _line(
            f"QUEUE: {len(s['active'])}",
            f"RETRY: {sum(1 for e in s['errors'] if e['event'] == 'RETRY')}  "
            f"ERRORS: {sum(1 for e in s['errors'] if e['event'] == 'WORKER_FAILED')}",
        )
    )
    out.append("└" + "─" * (W - 2) + "┘")
    return "\n".join(out)


def replay(job_id: str) -> str:
    """Reconstruit la chronologie exacte d'un job depuis le journal."""
    events = Journal(job_id).read()
    if not events:
        return f"Aucun journal pour {job_id} (cherché dans {cfgmod.LOG_DIR})"
    t0 = events[0]["mono"]
    lines = [f"REPLAY {job_id}  ({len(events)} événements)", "=" * 70]
    for e in events:
        rel = e["mono"] - t0
        extra = " ".join(
            f"{k}={v}"
            for k, v in e.items()
            if k not in ("ts", "mono", "pid", "job_id", "event", "metrics")
        )
        lines.append(f"{rel:9.3f}s  {e['event']:18s} {extra[:70]}")
        if e.get("metrics"):
            m = e["metrics"]
            lines.append(
                f"{'':11s}  └─ ttft={m.get('ttft_ms')}ms "
                f"dur={m.get('duration_ms')}ms tok/s={m.get('tokens_per_second')}"
            )
    state = cp.JobStore(job_id).load()
    if state:
        lines += ["=" * 70, f"ÉTAT FINAL: {state['status']}"]
        for t in state.get("tasks", []):
            lines.append(
                f"  {t['id']} {t['status']:8s} worker={t.get('worker')} "
                f"attempts={t.get('attempts')} out={t.get('output_hash')}"
            )
    return "\n".join(lines)


def watch(interval: float = 2.0, iterations: int = 0):
    i = 0
    try:
        while iterations == 0 or i < iterations:
            print("\033[2J\033[H" + render(probe=(i % 5 == 0)))
            i += 1
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nboard arrêté")
