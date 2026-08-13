"""Worker — une unité d'exécution (provider + modèle) observable et récupérable.

Un worker ne ment jamais sur son état : silencieux ≠ OK. Le heartbeat porte
last_activity, et un worker sans token depuis idle_timeout devient TIMEOUT.
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field

from .providers import UNAVAILABLE, Provider, Result

STATES = {
    "STARTING",
    "READY",
    "RUNNING",
    "WAITING",
    "COMPLETED",
    "FAILED",
    "TIMEOUT",
    "RECOVERING",
    "STOPPED",
}

# Erreurs qui justifient un retry aveugle (transitoires) vs celles qui non.
RETRYABLE = {
    "server_unavailable",
    "timeout_connect",
    "timeout_first_token",
    "timeout_idle",
    "timeout_request",
    "empty_response",
    "http_error",
}
# reasoning_only : relancer à l'identique reproduirait le même
# raisonnement sans réponse — il faut changer la requête, pas réessayer.
NON_RETRYABLE = {"model_unavailable", "cancelled", "reasoning_only"}


@dataclass
class Heartbeat:
    worker_id: str
    status: str = "STARTING"
    model: str = ""
    provider: str = ""
    last_activity: float = field(default_factory=time.time)
    last_token_at: float | None = None
    current_job: str | None = None
    current_task: str | None = None
    tokens: int = 0
    started_at: float | None = None
    detail: str = ""

    def age_s(self) -> float:
        return round(time.time() - self.last_activity, 2)

    def to_dict(self) -> dict:
        return {
            "worker": self.worker_id,
            "status": self.status,
            "provider": self.provider,
            "model": self.model,
            "job": self.current_job,
            "task": self.current_task,
            "tokens": self.tokens,
            "idle_s": self.age_s(),
            "last_token_ms": (
                round((time.time() - self.last_token_at) * 1000)
                if self.last_token_at
                else UNAVAILABLE
            ),
            "detail": self.detail,
        }


class Worker:
    def __init__(
        self,
        worker_id: str,
        provider: Provider,
        model: str,
        journal=None,
        retry: dict | None = None,
    ):
        self.id = worker_id
        self.provider = provider
        self.model = model
        self.journal = journal
        self.retry = retry or {"max_attempts": 3, "backoff_base_s": 1.5}
        self.hb = Heartbeat(worker_id=worker_id, model=model, provider=provider.name)
        self._lock = threading.Lock()
        self._current_request: str | None = None

    # -- santé -------------------------------------------------------------
    def health(self) -> dict:
        h = self.provider.health()
        st = self.provider.model_status(self.model)
        healthy = h["status"] == "up" and st == "AVAILABLE"
        self.hb.status = "READY" if healthy else "FAILED"
        self.hb.detail = f"server={h['status']} model={st}"
        self.hb.last_activity = time.time()
        return {
            "worker": self.id,
            "healthy": healthy,
            "server": h,
            "model_status": st,
            "model": self.model,
        }

    def cancel(self) -> bool:
        return bool(self._current_request) and self.provider.cancel(
            self._current_request
        )

    # -- exécution ---------------------------------------------------------
    def run(
        self,
        prompt: str,
        system: str | None = None,
        job_id: str | None = None,
        task_id: str | None = None,
        on_event=None,
        **opts,
    ) -> Result:
        """Exécute avec retry classifié. Renvoie toujours un Result (jamais None)."""
        messages = ([{"role": "system", "content": system}] if system else []) + [
            {"role": "user", "content": prompt}
        ]
        last: Result | None = None
        max_attempts = int(self.retry.get("max_attempts", 3))

        for attempt in range(1, max_attempts + 1):
            rid = uuid.uuid4().hex[:12]
            self._current_request = rid
            self.hb.status = "RUNNING"
            self.hb.current_job, self.hb.current_task = job_id, task_id
            self.hb.started_at = time.time()
            self.hb.tokens = 0
            self.hb.last_activity = time.time()
            self._emit(
                "WORKER_STARTED",
                worker=self.id,
                task=task_id,
                attempt=attempt,
                model=self.model,
                provider=self.provider.name,
                request_id=rid,
            )

            res: Result | None = None
            for ev in self.provider.stream(
                self.model, messages, request_id=rid, worker=self.id, **opts
            ):
                if ev["event"] == "FIRST_TOKEN":
                    self.hb.last_token_at = time.time()
                    self.hb.last_activity = time.time()
                    self._emit(
                        "FIRST_TOKEN", worker=self.id, task=task_id, request_id=rid
                    )
                    if on_event:
                        on_event(ev)
                elif ev["event"] == "TOKEN":
                    self.hb.tokens += 1
                    self.hb.last_token_at = time.time()
                    self.hb.last_activity = time.time()
                    if on_event:
                        on_event(ev)
                elif ev["event"] == "RESULT":
                    res = ev["result"]

            if res is None:  # ne devrait jamais arriver : _run_stream émet toujours
                res = Result(
                    request_id=rid,
                    provider=self.provider.name,
                    model=self.model,
                    worker=self.id,
                    status="http_error",
                    error="stream terminé sans RESULT",
                )
            res.worker = self.id
            last = res
            self._current_request = None

            if res.ok:
                self.hb.status = "COMPLETED"
                self.hb.detail = ""
                self._emit(
                    "WORKER_COMPLETED",
                    worker=self.id,
                    task=task_id,
                    request_id=rid,
                    metrics=res.metrics,
                    chars=len(res.content),
                )
                return res

            self.hb.status = "TIMEOUT" if res.status.startswith("timeout") else "FAILED"
            self.hb.detail = f"{res.status}: {res.error}"
            self._emit(
                "WORKER_FAILED",
                worker=self.id,
                task=task_id,
                request_id=rid,
                status=res.status,
                error=res.error,
            )

            if res.status in NON_RETRYABLE or attempt >= max_attempts:
                break
            backoff = float(self.retry.get("backoff_base_s", 1.5)) ** attempt
            self._emit(
                "RETRY",
                worker=self.id,
                task=task_id,
                attempt=attempt,
                backoff_s=round(backoff, 2),
                reason=res.status,
            )
            self.hb.status = "RECOVERING"
            time.sleep(backoff)

        return last

    def _emit(self, event: str, **fields):
        if self.journal:
            self.journal.emit(event, **fields)


def build_workers(cfg: dict, journal=None) -> dict[str, Worker]:
    """Construit les workers déclarés dans la config vérifiée."""
    from .providers import Timeouts, build_provider

    t = Timeouts(**cfg.get("timeouts", {}))
    workers: dict[str, Worker] = {}
    for slot, spec in cfg.get("workers", {}).items():
        alias = spec["provider"]
        pcfg = cfg["providers"].get(alias)
        if not pcfg:
            continue
        p = build_provider(pcfg["kind"], pcfg["base_url"], t)
        workers[slot] = Worker(
            slot, p, spec["model"], journal=journal, retry=cfg.get("retry")
        )
    return workers
