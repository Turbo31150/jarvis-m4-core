"""Checkpoints & reprise — état d'un job persisté à chaque étape.

Deux garanties, distinctes et toutes deux nécessaires :
  - contre un kill : écriture par temporaire + rename, le temporaire étant
    propre au processus (un `.tmp` partagé se fait renommer sous les pieds) ;
  - contre un autre processus : verrou `fcntl.flock` autour du read-modify-write.
    `run` et `watchdog --act` écrivent le même job — un threading.Lock ne les
    sépare pas, et la relecture de l'un écraserait la progression de l'autre.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .config import JOB_DIR

STATES = {
    "PENDING",
    "RUNNING",
    "SUCCESS",
    "FAILED",
    "RETRYING",
    "CANCELLED",
    "RECOVERABLE",
    "BLOCKED",
}

_LOCK = threading.Lock()


def sha(text: str) -> str:
    return hashlib.sha256((text or "").encode()).hexdigest()[:16]


def new_job_id(prefix: str = "job") -> str:
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:6]}"


class JobStore:
    def __init__(self, job_id: str, job_dir: Path | None = None):
        self.job_id = job_id
        self.dir = Path(job_dir or JOB_DIR)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / f"{job_id}.json"

    # -- persistance -------------------------------------------------------
    @contextmanager
    def _exclusive(self):
        """Verrou INTER-PROCESSUS autour d'un read-modify-write.

        `jarvis-dual run` et `jarvis-dual watchdog --act` sont deux processus
        distincts qui écrivent le même job : un threading.Lock ne les sépare
        pas. Sans flock, la relecture de l'un écrase la progression de l'autre.
        Le lock est pris sur un fichier dédié, jamais sur l'état lui-même
        (qui est remplacé par rename, donc son inode change).
        """
        self.dir.mkdir(parents=True, exist_ok=True)
        lock_path = self.path.with_suffix(".lock")
        with _LOCK:  # threads du processus courant
            with open(lock_path, "a+") as fh:
                fcntl.flock(fh, fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(fh, fcntl.LOCK_UN)

    def _write(self, state: dict):
        # Temporaire propre au processus : un `.tmp` partagé fait renommer à
        # un processus le fichier qu'un autre est en train d'écrire.
        tmp = self.path.with_suffix(f".tmp.{os.getpid()}")
        tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False, default=str))
        os.replace(tmp, self.path)

    def load(self) -> dict | None:
        if not self.path.exists():
            return None
        try:
            return json.loads(self.path.read_text())
        except json.JSONDecodeError:
            return None

    # -- cycle de vie ------------------------------------------------------
    def create(self, request: str, mode: str, tasks: list[dict]) -> dict:
        state = {
            "job_id": self.job_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "mode": mode,
            "request_hash": sha(request),
            "request_preview": (request or "")[:200],
            "status": "PENDING",
            "tasks": tasks,
        }
        with self._exclusive():
            self._write(state)
        return state

    def update_task(self, task_id: str, **fields) -> dict:
        with self._exclusive():
            state = self.load() or {}
            for t in state.get("tasks", []):
                if t["id"] == task_id:
                    t.update(fields)
                    t["updated_at"] = datetime.now(timezone.utc).isoformat()
                    break
            state["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._write(state)
            return state

    def set_status(self, status: str) -> dict:
        with self._exclusive():
            state = self.load() or {}
            state["status"] = status
            state["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._write(state)
            return state

    # -- reprise -----------------------------------------------------------
    def pending_tasks(self) -> list[dict]:
        """Tâches à (re)faire : tout ce qui n'a pas atteint SUCCESS."""
        state = self.load() or {}
        return [t for t in state.get("tasks", []) if t.get("status") != "SUCCESS"]

    def resumable(self) -> bool:
        state = self.load()
        return bool(
            state
            and state.get("status") not in ("SUCCESS", "CANCELLED")
            and self.pending_tasks()
        )


def make_task(
    idx: int,
    prompt: str,
    owner: str = "auto",
    depends_on=None,
    risk: str = "low",
    files=None,
) -> dict:
    return {
        "id": f"TASK-{idx:03d}",
        "prompt": prompt,
        "owner": owner,
        "depends_on": depends_on or [],
        "files": files or [],
        "risk": risk,
        "status": "PENDING",
        "attempts": 0,
        "input_hash": sha(prompt),
        "output_hash": None,
        "worker": None,
        "result": None,
        "checkpoint": None,
    }


def list_jobs(job_dir: Path | None = None) -> list[dict]:
    d = Path(job_dir or JOB_DIR)
    if not d.exists():
        return []
    out = []
    for p in sorted(d.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            j = json.loads(p.read_text())
        except json.JSONDecodeError:
            continue
        done = sum(1 for t in j.get("tasks", []) if t.get("status") == "SUCCESS")
        out.append(
            {
                "job_id": j.get("job_id", p.stem),
                "status": j.get("status", "UNKNOWN"),
                "mode": j.get("mode", "?"),
                "progress": f"{done}/{len(j.get('tasks', []))}",
                "updated_at": j.get("updated_at", ""),
                "mtime": p.stat().st_mtime,
            }
        )
    return out


def stale_jobs(max_age_s: float = 600.0, job_dir: Path | None = None) -> list[dict]:
    """Jobs RUNNING sans écriture récente = candidats watchdog."""
    now = time.time()
    return [
        j
        for j in list_jobs(job_dir)
        if j["status"] in ("RUNNING", "PENDING") and now - j["mtime"] > max_age_s
    ]
