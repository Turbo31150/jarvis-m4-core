"""Adapters providers — couche unique d'accès aux backends d'inférence.

Aucun autre module ne doit connaître une URL, un timeout ou un retry.
Stdlib uniquement (http.client) pour maîtriser les 4 timeouts distincts :
connect / first_token / idle / request.

Statuts renvoyés (jamais inventés) :
  success | empty_response | reasoning_only | model_unavailable | server_unavailable
  | timeout_connect | timeout_first_token | timeout_idle | timeout_request
  | http_error | cancelled
"""

from __future__ import annotations

import http.client
import json
import socket
import threading
import time
import uuid
from dataclasses import dataclass, field
from urllib.parse import urlparse

UNAVAILABLE = "UNAVAILABLE"


@dataclass
class Timeouts:
    connect: float = 5.0
    first_token: float = 60.0
    idle: float = 30.0
    request: float = 300.0


@dataclass
class Result:
    """Sortie normalisée d'un worker. Aucune métrique n'est inventée."""

    request_id: str
    provider: str
    model: str
    status: str
    content: str = ""
    worker: str | None = None
    error: str | None = None
    metrics: dict = field(default_factory=dict)
    events: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status == "success"

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "worker": self.worker,
            "provider": self.provider,
            "model": self.model,
            "status": self.status,
            "content": self.content,
            "metrics": self.metrics,
            "error": self.error,
        }


class Provider:
    """Contrat commun. Sous-classer pour chaque backend réel."""

    name = "abstract"
    # Chaque backend coupe le raisonnement à sa façon : le message d'erreur
    # doit nommer LE bon réglage, pas celui du voisin.
    THINK_OFF_HINT = "consulter la documentation du backend"

    def __init__(self, base_url: str, timeouts: Timeouts | None = None, journal=None):
        self.base_url = base_url.rstrip("/")
        self.timeouts = timeouts or Timeouts()
        self.journal = journal
        u = urlparse(self.base_url)
        self._host = u.hostname
        self._port = u.port or (443 if u.scheme == "https" else 80)
        self._https = u.scheme == "https"
        self._cancel: dict[str, threading.Event] = {}

    # -- transport ---------------------------------------------------------
    def _conn(self, timeout: float) -> http.client.HTTPConnection:
        cls = http.client.HTTPSConnection if self._https else http.client.HTTPConnection
        return cls(self._host, self._port, timeout=timeout)

    def _get_json(self, path: str, timeout: float | None = None):
        c = self._conn(timeout or self.timeouts.connect)
        try:
            c.request("GET", path)
            r = c.getresponse()
            body = r.read()
            if r.status >= 400:
                raise RuntimeError(f"HTTP {r.status}")
            return json.loads(body)
        finally:
            c.close()

    # -- API publique ------------------------------------------------------
    def health(self) -> dict:
        """{'status': 'up'|'down', 'detail': str, 'latency_ms': int|UNAVAILABLE}"""
        t0 = time.perf_counter()
        try:
            self.discover_models()
            return {
                "status": "up",
                "detail": "models endpoint reachable",
                "latency_ms": int((time.perf_counter() - t0) * 1000),
            }
        except Exception as e:  # noqa: BLE001 - on rapporte la cause telle quelle
            return {
                "status": "down",
                "detail": f"{type(e).__name__}: {e}",
                "latency_ms": UNAVAILABLE,
            }

    def discover_models(self) -> list[str]:
        raise NotImplementedError

    def model_status(self, model: str) -> str:
        """AVAILABLE | UNAVAILABLE | UNKNOWN — d'après la découverte seule.

        Un modèle listé n'est PAS une preuve qu'il répond : seule une inférence
        réelle le prouve (cf. doctor.py, test du modèle fantôme).
        """
        try:
            return "AVAILABLE" if model in self.discover_models() else "UNAVAILABLE"
        except Exception:  # noqa: BLE001
            return "UNKNOWN"

    def cancel(self, request_id: str) -> bool:
        ev = self._cancel.get(request_id)
        if ev:
            ev.set()
            return True
        return False

    def chat(self, model, messages, request_id=None, worker=None, **opts) -> Result:
        """Non-streaming logique : consomme le stream et agrège."""
        content = []
        res = None
        for ev in self.stream(
            model, messages, request_id=request_id, worker=worker, **opts
        ):
            if ev["event"] == "TOKEN":
                content.append(ev["text"])
            elif ev["event"] == "RESULT":
                res = ev["result"]
        if res is not None:
            res.content = "".join(content) or res.content
        return res

    def stream(self, model, messages, request_id=None, worker=None, **opts):
        raise NotImplementedError

    # -- helpers communs ---------------------------------------------------
    def _run_stream(
        self, path, payload, model, request_id, worker, parse_line, extract_usage
    ):
        """Boucle de streaming commune : timeouts distincts + métriques réelles."""
        rid = request_id or uuid.uuid4().hex[:12]
        cancel = threading.Event()
        self._cancel[rid] = cancel
        t_start = time.perf_counter()
        ttft = None
        ntok = 0
        nreason = 0
        chunks: list[str] = []
        usage: dict = {}
        conn = None

        def result(status, error=None):
            dur = (time.perf_counter() - t_start) * 1000
            m = {
                "ttft_ms": round(ttft * 1000, 1) if ttft is not None else UNAVAILABLE,
                "duration_ms": round(dur, 1),
                "stream_chunks": ntok,
                "prompt_tokens": usage.get("prompt_tokens", UNAVAILABLE),
                "completion_tokens": usage.get("completion_tokens", UNAVAILABLE),
                "total_tokens": usage.get("total_tokens", UNAVAILABLE),
            }
            ct = usage.get("completion_tokens")
            if isinstance(ct, int) and ttft is not None and dur / 1000 > ttft:
                m["tokens_per_second"] = round(ct / ((dur / 1000) - ttft), 2)
            elif ntok and ttft is not None and dur / 1000 > ttft:
                # pas d'usage fourni : débit de chunks, explicitement nommé
                m["chunks_per_second"] = round(ntok / ((dur / 1000) - ttft), 2)
                m["tokens_per_second"] = UNAVAILABLE
            else:
                m["tokens_per_second"] = UNAVAILABLE
            return Result(
                request_id=rid,
                provider=self.name,
                model=model,
                worker=worker,
                status=status,
                content="".join(chunks),
                error=error,
                metrics=m,
            )

        try:
            conn = self._conn(self.timeouts.connect)
            body = json.dumps(payload).encode()
            try:
                conn.request(
                    "POST",
                    path,
                    body=body,
                    headers={"Content-Type": "application/json"},
                )
            except (socket.timeout, TimeoutError):
                yield {
                    "event": "RESULT",
                    "result": result("timeout_connect", "connect timeout"),
                }
                return
            except (ConnectionRefusedError, OSError) as e:
                yield {
                    "event": "RESULT",
                    "result": result("server_unavailable", f"{type(e).__name__}: {e}"),
                }
                return

            if conn.sock:
                conn.sock.settimeout(self.timeouts.first_token)
            try:
                resp = conn.getresponse()
            except (socket.timeout, TimeoutError):
                yield {
                    "event": "RESULT",
                    "result": result("timeout_first_token", "no response headers"),
                }
                return

            if resp.status >= 400:
                raw = resp.read().decode("utf-8", "replace")[:400]
                st = "model_unavailable" if resp.status in (404, 400) else "http_error"
                yield {
                    "event": "RESULT",
                    "result": result(st, f"HTTP {resp.status}: {raw}"),
                }
                return

            for raw in resp:
                if cancel.is_set():
                    yield {
                        "event": "RESULT",
                        "result": result("cancelled", "cancelled by caller"),
                    }
                    return
                if (time.perf_counter() - t_start) > self.timeouts.request:
                    yield {
                        "event": "RESULT",
                        "result": result("timeout_request", "global request timeout"),
                    }
                    return
                line = raw.decode("utf-8", "replace").strip()
                if not line:
                    continue
                parsed = parse_line(line)
                piece, done, u = parsed[0], parsed[1], parsed[2]
                if len(parsed) > 3 and parsed[3]:
                    nreason += len(parsed[3])
                if u:
                    usage.update(u)
                if piece:
                    if ttft is None:
                        ttft = time.perf_counter() - t_start
                        if conn.sock:
                            conn.sock.settimeout(self.timeouts.idle)
                        yield {
                            "event": "FIRST_TOKEN",
                            "t": time.time(),
                            "request_id": rid,
                            "worker": worker,
                            "text": piece,
                        }
                    ntok += 1
                    chunks.append(piece)
                    yield {
                        "event": "TOKEN",
                        "t": time.time(),
                        "request_id": rid,
                        "worker": worker,
                        "text": piece,
                    }
                if done:
                    break

            usage.update(extract_usage(usage))
            if not chunks:
                if nreason:
                    yield {
                        "event": "RESULT",
                        "result": result(
                            "reasoning_only",
                            f"le modèle est en mode thinking : {nreason} caractères "
                            f"de raisonnement, aucun contenu. Couper le raisonnement "
                            f"({self.THINK_OFF_HINT}) ou augmenter max_tokens.",
                        ),
                    }
                    return
                yield {
                    "event": "RESULT",
                    "result": result("empty_response", "HTTP 200 mais contenu vide"),
                }
                return
            yield {"event": "RESULT", "result": result("success")}
        except (socket.timeout, TimeoutError):
            st = "timeout_first_token" if ttft is None else "timeout_idle"
            yield {"event": "RESULT", "result": result(st, "socket timeout")}
        except Exception as e:  # noqa: BLE001
            yield {
                "event": "RESULT",
                "result": result("http_error", f"{type(e).__name__}: {e}"),
            }
        finally:
            self._cancel.pop(rid, None)
            if conn:
                try:
                    conn.close()
                except Exception:  # noqa: BLE001
                    pass


class LMStudioProvider(Provider):
    """LM Studio — endpoint OpenAI-compatible /v1 (vérifié sur cette machine)."""

    name = "lmstudio"
    THINK_OFF_HINT = "no_think=True"

    def discover_models(self) -> list[str]:
        d = self._get_json("/v1/models")
        return [m["id"] for m in d.get("data", [])]

    def loaded_models(self) -> list[str]:
        """Modèles RÉSIDENTS en mémoire, via l'endpoint natif /api/v0/models.

        Décisif sur un GPU étroit : LM Studio ne décharge pas le modèle courant
        avant d'en charger un autre, donc toute demande visant un modèle
        `not-loaded` échoue en cudaMalloc OOM. Ce n'est pas un modèle cassé,
        c'est un modèle qui n'est pas là. Liste vide si l'endpoint n'existe pas.
        """
        try:
            d = self._get_json("/api/v0/models")
        except Exception:  # noqa: BLE001 - endpoint absent selon la version
            return []
        return [m["id"] for m in d.get("data", []) if m.get("state") == "loaded"]

    def stream(self, model, messages, request_id=None, worker=None, **opts):
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        for k in ("temperature", "max_tokens", "top_p", "seed"):
            if k in opts and opts[k] is not None:
                payload[k] = opts[k]
        if opts.get("no_think") and payload["messages"]:
            # Suffixe reconnu par les qwen3* pour couper le raisonnement.
            last = dict(payload["messages"][-1])
            last["content"] = f"{last.get('content', '')} /no_think".strip()
            payload["messages"] = payload["messages"][:-1] + [last]

        def parse(line):
            if not line.startswith("data:"):
                return None, False, None
            data = line[5:].strip()
            if data == "[DONE]":
                return None, True, None
            try:
                j = json.loads(data)
            except json.JSONDecodeError:
                return None, False, None
            u = None
            if j.get("usage"):
                u = {
                    "prompt_tokens": j["usage"].get("prompt_tokens", UNAVAILABLE),
                    "completion_tokens": j["usage"].get(
                        "completion_tokens", UNAVAILABLE
                    ),
                    "total_tokens": j["usage"].get("total_tokens", UNAVAILABLE),
                }
            ch = (j.get("choices") or [{}])[0]
            delta = ch.get("delta") or {}
            # Les modèles qwen3* émettent leur raisonnement dans un champ
            # séparé : sans contenu ET sans le compter, on conclut à tort
            # « réponse vide » alors que le modèle travaille.
            return (
                delta.get("content"),
                False,
                u,
                delta.get("reasoning_content") or delta.get("reasoning"),
            )

        yield from self._run_stream(
            "/v1/chat/completions",
            payload,
            model,
            request_id,
            worker,
            parse,
            lambda u: {},
        )


class OllamaProvider(Provider):
    """Ollama — /api/chat, NDJSON. Fournit des compteurs de tokens réels."""

    name = "ollama"
    THINK_OFF_HINT = "think=False"

    def discover_models(self) -> list[str]:
        d = self._get_json("/api/tags")
        return [m["name"] for m in d.get("models", [])]

    def stream(self, model, messages, request_id=None, worker=None, **opts):
        payload = {"model": model, "messages": messages, "stream": True}
        options = {}
        if opts.get("temperature") is not None:
            options["temperature"] = opts["temperature"]
        if opts.get("max_tokens") is not None:
            options["num_predict"] = opts["max_tokens"]
        if options:
            payload["options"] = options
        if opts.get("think") is False:
            payload["think"] = False

        def parse(line):
            try:
                j = json.loads(line)
            except json.JSONDecodeError:
                return None, False, None
            if j.get("error"):
                raise RuntimeError(j["error"])
            u = None
            if j.get("done"):
                u = {
                    "prompt_tokens": j.get("prompt_eval_count", UNAVAILABLE),
                    "completion_tokens": j.get("eval_count", UNAVAILABLE),
                    "eval_duration_ns": j.get("eval_duration", UNAVAILABLE),
                }
                if isinstance(u["prompt_tokens"], int) and isinstance(
                    u["completion_tokens"], int
                ):
                    u["total_tokens"] = u["prompt_tokens"] + u["completion_tokens"]
            msg = j.get("message") or {}
            # Ollama place le raisonnement dans `thinking` : sans le compter,
            # un modèle qwen3 qui réfléchit passe pour une réponse vide.
            return msg.get("content"), bool(j.get("done")), u, msg.get("thinking")

        yield from self._run_stream(
            "/api/chat", payload, model, request_id, worker, parse, lambda u: {}
        )


PROVIDERS = {"lmstudio": LMStudioProvider, "ollama": OllamaProvider}


def _register_cli_providers():
    """Providers pilotés par un binaire local (import tardif : dépendance inverse)."""
    from .providers_cli import AgyProvider

    PROVIDERS.setdefault("agy", AgyProvider)


_register_cli_providers()


def build_provider(
    kind: str, base_url: str, timeouts: Timeouts | None = None
) -> Provider:
    if kind not in PROVIDERS:
        raise ValueError(f"provider inconnu: {kind} (connus: {sorted(PROVIDERS)})")
    return PROVIDERS[kind](base_url, timeouts)
