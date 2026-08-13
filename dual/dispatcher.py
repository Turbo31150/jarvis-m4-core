"""DualDispatcher — modes d'exécution, micro-tâches, agrégation, reprise.

Le parallélisme est RÉEL (threads sur I/O réseau, deux backends distincts).
La preuve est dans le journal : entrelacement des FIRST_TOKEN/WORKER_COMPLETED.
"""

from __future__ import annotations

import re
import threading
from concurrent.futures import ThreadPoolExecutor

from . import checkpoint as cp
from .journal import Journal
from .worker import Worker, build_workers

MODES = ("single", "parallel", "cascade", "review", "fallback", "pipeline")


class DualDispatcher:
    def __init__(self, cfg: dict, job_id: str | None = None):
        self.cfg = cfg
        self.job_id = job_id or cp.new_job_id()
        self.journal = Journal(self.job_id)
        self.workers: dict[str, Worker] = build_workers(cfg, journal=self.journal)
        self.store = cp.JobStore(self.job_id)
        self._lock = threading.Lock()

    # -- introspection -----------------------------------------------------
    @property
    def available(self) -> list[str]:
        return list(self.workers)

    def heartbeats(self) -> list[dict]:
        return [w.hb.to_dict() for w in self.workers.values()]

    # -- découpage ---------------------------------------------------------
    @staticmethod
    def split(request: str, max_tasks: int = 8) -> list[str]:
        """Découpe une demande en micro-tâches.

        Règle conservatrice : on ne découpe QUE sur des marqueurs explicites
        (lignes numérotées / puces). Sinon, une tâche unique — mieux vaut une
        grosse tâche qu'un découpage inventé qui perd le sens.
        """
        lines = [l.strip() for l in (request or "").splitlines() if l.strip()]
        items = [
            re.sub(r"^(\d+[.)]|[-*•])\s*", "", l)
            for l in lines
            if re.match(r"^(\d+[.)]|[-*•])\s+", l)
        ]
        items = [i for i in items if len(i) > 3]
        return items[:max_tasks] if len(items) >= 2 else [request]

    # -- exécution ---------------------------------------------------------
    def run(
        self,
        request: str,
        mode: str = "single",
        system: str | None = None,
        resume: bool = False,
        **opts,
    ) -> dict:
        if mode not in MODES:
            raise ValueError(f"mode inconnu: {mode} (connus: {MODES})")
        if not self.workers:
            return {
                "job_id": self.job_id,
                "status": "BLOCKED",
                "error": "aucun worker disponible",
                "results": [],
            }

        prompts = self.split(request)
        if resume and self.store.load():
            state = self.store.load()
            todo = self.store.pending_tasks()
            self.journal.emit(
                "RECOVERY",
                job_id=self.job_id,
                pending=len(todo),
                total=len(state.get("tasks", [])),
            )
        else:
            tasks = [cp.make_task(i + 1, p) for i, p in enumerate(prompts)]
            self.store.create(request, mode, tasks)
            self.journal.emit(
                "JOB_CREATED", mode=mode, tasks=len(tasks), workers=self.available
            )
            todo = tasks

        self.store.set_status("RUNNING")
        handler = getattr(self, f"_mode_{mode}")
        results = handler(todo, system, **opts)

        ok = all(r.get("status") == "success" for r in results) and bool(results)
        self.store.set_status("SUCCESS" if ok else "FAILED")
        self.journal.emit(
            "JOB_COMPLETED", status="SUCCESS" if ok else "FAILED", tasks=len(results)
        )
        return {
            "job_id": self.job_id,
            "mode": mode,
            "status": "SUCCESS" if ok else "FAILED",
            "results": results,
            "journal": str(self.journal.path),
            "checkpoint": str(self.store.path),
        }

    # -- helpers -----------------------------------------------------------
    def _exec(self, worker: Worker, task: dict, system, **opts):
        self.journal.emit(
            "TASK_DISPATCHED", task=task["id"], worker=worker.id, model=worker.model
        )
        self.store.update_task(
            task["id"],
            status="RUNNING",
            worker=worker.id,
            attempts=task.get("attempts", 0) + 1,
        )
        res = worker.run(
            task["prompt"],
            system=system,
            job_id=self.job_id,
            task_id=task["id"],
            **opts,
        )
        d = res.to_dict()
        d["task"] = task["id"]
        self.store.update_task(
            task["id"],
            status="SUCCESS" if res.ok else "FAILED",
            output_hash=cp.sha(res.content),
            result=d,
            checkpoint={"worker": worker.id, "metrics": res.metrics},
        )
        self.journal.emit(
            "CHECKPOINT", task=task["id"], status=d["status"], worker=worker.id
        )
        return d

    def _pick(self, *slots) -> list[Worker]:
        return [self.workers[s] for s in slots if s in self.workers]

    # -- modes -------------------------------------------------------------
    def _mode_single(self, tasks, system, **opts):
        w = self._pick("worker_a", "worker_b")[0]
        return [self._exec(w, t, system, **opts) for t in tasks]

    def _mode_parallel(self, tasks, system, **opts):
        """A et B traitent la MÊME tâche simultanément (preuve de concurrence)."""
        ws = self._pick("worker_a", "worker_b")
        if len(ws) < 2:
            self.journal.emit(
                "FALLBACK", reason="un seul worker disponible", mode="parallel->single"
            )
            return self._mode_single(tasks, system, **opts)
        out = []
        for t in tasks:
            with ThreadPoolExecutor(max_workers=len(ws)) as ex:
                futs = [ex.submit(self._exec, w, t, system, **opts) for w in ws]
                out.extend(f.result() for f in futs)
        return out

    def _mode_fallback(self, tasks, system, **opts):
        ws = self._pick("worker_a", "worker_b")
        out = []
        for t in tasks:
            for i, w in enumerate(ws):
                if i:
                    self.journal.emit("FALLBACK", task=t["id"], to=w.id)
                d = self._exec(w, t, system, **opts)
                if d["status"] == "success":
                    break
            out.append(d)
        return out

    def _mode_cascade(self, tasks, system, **opts):
        """A produit → B reprend le résultat de A, étape par étape, avec checkpoint."""
        ws = self._pick("worker_a", "worker_b")
        out, carry = [], None
        for t in tasks:
            for w in ws:
                task = dict(t)
                if carry:
                    task["prompt"] = (
                        f"{t['prompt']}\n\n[Résultat de l'étape précédente]\n"
                        f"{carry[:4000]}"
                    )
                    task["id"] = f"{t['id']}-{w.id[-1].upper()}"
                d = self._exec(w, task, system, **opts)
                out.append(d)
                if d["status"] != "success":
                    return out  # on stoppe la cascade, l'état reste reprenable
                carry = d["content"]
        return out

    def _mode_review(self, tasks, system, **opts):
        """A produit, B critique, A corrige."""
        ws = self._pick("worker_a", "worker_b")
        if len(ws) < 2:
            return self._mode_single(tasks, system, **opts)
        a, b = ws[0], ws[1]
        out = []
        for t in tasks:
            prod = self._exec(a, t, system, **opts)
            out.append(prod)
            if prod["status"] != "success":
                continue
            crit = self._exec(
                b,
                {
                    **t,
                    "id": f"{t['id']}-REVIEW",
                    "prompt": f"Critique ce travail. Liste UNIQUEMENT les erreurs "
                    f"factuelles et manques.\n\nDemande:\n{t['prompt']}\n\n"
                    f"Travail:\n{prod['content'][:4000]}",
                },
                system,
                **opts,
            )
            out.append(crit)
            if crit["status"] != "success":
                continue
            fix = self._exec(
                a,
                {
                    **t,
                    "id": f"{t['id']}-FIX",
                    "prompt": f"Corrige ton travail selon la critique.\n\nDemande:\n"
                    f"{t['prompt']}\n\nTravail:\n{prod['content'][:3000]}\n\n"
                    f"Critique:\n{crit['content'][:2000]}",
                },
                system,
                **opts,
            )
            out.append(fix)
        return out

    def _mode_pipeline(self, tasks, system, **opts):
        """Chaque tâche va au worker suivant, sans barrière entre les tâches."""
        ws = self._pick("worker_a", "worker_b")
        with ThreadPoolExecutor(max_workers=max(1, len(ws))) as ex:
            futs = [
                ex.submit(self._exec, ws[i % len(ws)], t, system, **opts)
                for i, t in enumerate(tasks)
            ]
            return [f.result() for f in futs]


def aggregate(results: list[dict], strategy: str = "first") -> dict:
    """Agrégateur. `strategy` : first | best | merge | consensus."""
    ok = [r for r in results if r.get("status") == "success"]
    if not ok:
        return {
            "strategy": strategy,
            "status": "FAILED",
            "content": "",
            "reason": "aucun résultat en succès",
        }
    if strategy == "first":
        pick = ok[0]
    elif strategy == "best":

        def score(r):
            m = r.get("metrics", {})
            tt = m.get("ttft_ms")
            return (
                len(r.get("content", "")),
                -(tt if isinstance(tt, (int, float)) else 1e9),
            )

        pick = max(ok, key=score)
    elif strategy == "merge":
        body = "\n\n".join(
            f"### {r['worker']} ({r['model']})\n{r['content']}" for r in ok
        )
        return {
            "strategy": strategy,
            "status": "SUCCESS",
            "content": body,
            "sources": [r["worker"] for r in ok],
        }
    elif strategy == "consensus":
        norm = {}
        for r in ok:
            norm.setdefault(r["content"].strip().lower()[:200], []).append(r["worker"])
        top = max(norm.items(), key=lambda kv: len(kv[1]))
        agree = len(top[1]) >= 2
        pick = ok[0]
        return {
            "strategy": strategy,
            "status": "SUCCESS",
            "content": pick["content"],
            "consensus": agree,
            "agreeing_workers": top[1],
        }
    else:
        raise ValueError(f"stratégie inconnue: {strategy}")
    return {
        "strategy": strategy,
        "status": "SUCCESS",
        "content": pick["content"],
        "worker": pick["worker"],
        "model": pick["model"],
        "metrics": pick["metrics"],
    }
