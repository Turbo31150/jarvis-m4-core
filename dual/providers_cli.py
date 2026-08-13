"""Providers pilotés par un CLI local (pas HTTP).

Cas d'usage : `agy` (Antigravity CLI, authentifié compte Google) donne accès à
Gemini/Claude/GPT-OSS sans facturation API. Sur cette machine, c'est le seul
worker rapide et fiable — le GPU 4 Go ne tient qu'un petit modèle local.

Le CLI n'expose pas de flux token par token : on lit stdout ligne par ligne.
Le TTFT mesuré est donc le **temps jusqu'à la première ligne**, pas jusqu'au
premier token — le champ est nommé `ttft_ms` mais `granularity` le précise, pour
ne pas laisser croire à une mesure qu'on n'a pas.
"""

from __future__ import annotations

import shutil
import subprocess
import time
import uuid

from .providers import UNAVAILABLE, Provider, Result


class CLIProvider(Provider):
    """Base des providers en sous-processus."""

    name = "cli"
    binary = ""

    def __init__(
        self,
        base_url: str = "",
        timeouts=None,
        journal=None,
        binary: str | None = None,
        default_model: str | None = None,
    ):
        super().__init__(base_url or "cli://local", timeouts, journal)
        self.binary = binary or self.binary
        self.default_model = default_model
        self._procs: dict[str, subprocess.Popen] = {}

    def _which(self) -> str | None:
        return shutil.which(self.binary)

    def health(self) -> dict:
        path = self._which()
        if not path:
            return {
                "status": "down",
                "detail": f"{self.binary} absent du PATH",
                "latency_ms": UNAVAILABLE,
            }
        t0 = time.perf_counter()
        try:
            models = self.discover_models()
        except Exception as e:  # noqa: BLE001
            return {
                "status": "down",
                "detail": f"{type(e).__name__}: {e}",
                "latency_ms": UNAVAILABLE,
            }
        return {
            "status": "up" if models else "down",
            "detail": f"{path} — {len(models)} modèle(s)",
            "latency_ms": int((time.perf_counter() - t0) * 1000),
        }

    def cancel(self, request_id: str) -> bool:
        p = self._procs.get(request_id)
        if p and p.poll() is None:
            p.terminate()
            return True
        return False

    def _argv(self, model: str, prompt: str, **opts) -> list[str]:
        raise NotImplementedError

    def stream(self, model, messages, request_id=None, worker=None, **opts):
        rid = request_id or uuid.uuid4().hex[:12]
        prompt = "\n\n".join(m["content"] for m in messages if m.get("content"))
        t0 = time.perf_counter()
        ttft = None
        chunks: list[str] = []

        def result(status, error=None):
            dur = (time.perf_counter() - t0) * 1000
            return Result(
                request_id=rid,
                provider=self.name,
                model=model,
                worker=worker,
                status=status,
                content="".join(chunks),
                error=error,
                metrics={
                    "ttft_ms": round(ttft * 1000, 1)
                    if ttft is not None
                    else UNAVAILABLE,
                    "duration_ms": round(dur, 1),
                    "granularity": "ligne (le CLI ne streame pas les tokens)",
                    "prompt_tokens": UNAVAILABLE,
                    "completion_tokens": UNAVAILABLE,
                    "total_tokens": UNAVAILABLE,
                    "tokens_per_second": UNAVAILABLE,
                    "stream_chunks": len(chunks),
                },
            )

        if not self._which():
            yield {
                "event": "RESULT",
                "result": result("server_unavailable", f"{self.binary} introuvable"),
            }
            return

        try:
            proc = subprocess.Popen(
                self._argv(model, prompt, **opts),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except OSError as e:
            yield {
                "event": "RESULT",
                "result": result("server_unavailable", f"{type(e).__name__}: {e}"),
            }
            return

        self._procs[rid] = proc
        try:
            for line in proc.stdout:
                if (time.perf_counter() - t0) > self.timeouts.request:
                    proc.terminate()
                    yield {
                        "event": "RESULT",
                        "result": result("timeout_request", "dépassement global"),
                    }
                    return
                if ttft is None:
                    if not line.strip():
                        continue
                    ttft = time.perf_counter() - t0
                    yield {
                        "event": "FIRST_TOKEN",
                        "t": time.time(),
                        "request_id": rid,
                        "worker": worker,
                        "text": line,
                    }
                chunks.append(line)
                yield {
                    "event": "TOKEN",
                    "t": time.time(),
                    "request_id": rid,
                    "worker": worker,
                    "text": line,
                }
            rc = proc.wait(timeout=10)
            err = (proc.stderr.read() or "").strip()[:300]
        except subprocess.TimeoutExpired:
            proc.kill()
            yield {
                "event": "RESULT",
                "result": result("timeout_request", "processus figé"),
            }
            return
        finally:
            self._procs.pop(rid, None)

        text = "".join(chunks).strip()
        if rc != 0:
            status = "model_unavailable" if "model" in err.lower() else "http_error"
            yield {"event": "RESULT", "result": result(status, f"rc={rc}: {err}")}
        elif not text:
            yield {
                "event": "RESULT",
                "result": result("empty_response", "sortie vide malgré rc=0"),
            }
        else:
            yield {"event": "RESULT", "result": result("success")}


class AgyProvider(CLIProvider):
    """Antigravity CLI (`agy`). Nécessite une session authentifiée."""

    name = "agy"
    binary = "agy"

    _models_cache: list[str] | None = None

    def discover_models(self) -> list[str]:
        # `agy models` fait un aller-retour réseau authentifié (~10-20 s, plus
        # si la machine est chargée) : on met en cache pour ne pas le payer à
        # chaque health check.
        if self._models_cache:
            return self._models_cache
        p = subprocess.run(
            [self.binary, "models"],
            capture_output=True,
            text=True,
            timeout=max(120, self.timeouts.request / 2),
        )
        if p.returncode != 0:
            raise RuntimeError((p.stderr or p.stdout).strip()[:200])
        out = []
        for line in p.stdout.splitlines():
            if "\t" in line:
                out.append(line.split("\t", 1)[0].strip())
        if not out:
            raise RuntimeError("aucun modèle — session non authentifiée ?")
        self._models_cache = out
        return out

    def _argv(self, model, prompt, **opts):
        argv = [
            self.binary,
            "-p",
            prompt,
            "--model",
            model,
            "--print-timeout",
            f"{int(self.timeouts.request)}s",
        ]
        if opts.get("effort") in ("low", "medium", "high"):
            argv += ["--effort", opts["effort"]]
        return argv
