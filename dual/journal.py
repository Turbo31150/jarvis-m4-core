"""Journal structuré (JSONL) — une ligne = un événement horodaté.

Sert à trois choses : le board, le replay, et la PREUVE de parallélisme.
Aucun secret ne doit transiter ici (les prompts sont tronqués).
"""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from .config import LOG_DIR

EVENTS = {
    "JOB_CREATED",
    "TASK_CREATED",
    "TASK_DISPATCHED",
    "WORKER_STARTED",
    "MODEL_READY",
    "FIRST_TOKEN",
    "TOKEN_STREAM",
    "WORKER_COMPLETED",
    "WORKER_FAILED",
    "RETRY",
    "FALLBACK",
    "CHECKPOINT",
    "RECOVERY",
    "JOB_COMPLETED",
    "WATCHDOG",
    "DIAGNOSTIC",
}

_LOCK = threading.Lock()


class Journal:
    def __init__(self, job_id: str, log_dir: Path | None = None):
        self.job_id = job_id
        self.dir = Path(log_dir or LOG_DIR)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / f"{job_id}.jsonl"

    def emit(self, event: str, **fields):
        if event not in EVENTS:
            fields["_unknown_event"] = True
        rec = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "mono": round(time.perf_counter(), 6),
            "pid": os.getpid(),
            "job_id": self.job_id,
            "event": event,
        }
        rec.update(fields)
        line = json.dumps(rec, ensure_ascii=False, default=str)
        with _LOCK:
            with self.path.open("a") as f:
                f.write(line + "\n")
        return rec

    def read(self) -> list[dict]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text().splitlines():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out


def list_jobs(log_dir: Path | None = None) -> list[str]:
    d = Path(log_dir or LOG_DIR)
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob("*.jsonl"))
