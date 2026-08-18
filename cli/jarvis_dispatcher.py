#!/usr/bin/env python3
"""
JARVIS Dispatcher unifié — façade Python unique pour TOUT appel LLM.
====================================================================
Phase 1.1 de la roadmap. Remplace à terme les 7 routers concurrents
(lm-ask.sh, model_router.sh, telegram_llm_router, router_bridge, etc.).

Principe : ne RÉIMPLÉMENTE PAS la cascade — il route vers le proxy unifié
`chat_proxy.js` (http://127.0.0.1:18800) qui porte déjà la cascade
lmstudio-m1 → ollama → ollama-cloud → lmstudio-m2 → gemini.
Ajoute par-dessus : circuit-breaker + retry/backoff, et un fallback DIRECT
(Ollama local → Ollama Cloud) si le proxy lui-même est down, pour qu'il n'y
ait jamais de SPOF total même en mono-machine M1.

Usage Python :
    from cli.jarvis_dispatcher import ask
    r = ask("explique X", mode="reason")
    print(r["text"], r["backend"], r["latency_ms"], r["ok"])

Usage CLI :
    python3 cli/jarvis_dispatcher.py "mon prompt" --mode fast
    python3 cli/jarvis_dispatcher.py --serve-metrics [--port 9109]

Routing déclaratif (recommandation C4 #2) :
    Fichier OPTIONNEL ~/.jarvis/dispatcher_routes.json (override JSON_DIR via
    JARVIS_ROUTES). Choix de JSON et non YAML : on reste "zero-dependency"
    (stdlib pure, json est inclus, pas de pyyaml/ruamel à installer). Absent →
    comportement actuel strictement inchangé. Schéma (toutes clés optionnelles) :
        {
          "proxy_url":   "http://127.0.0.1:18800/v1/chat/completions",
          "ollama_url":  "http://127.0.0.1:11434/api/chat",
          "cloud_model": "gpt-oss:20b-cloud",
          "mode_models": { "reason": ["proxy-model", "ollama-fallback"], ... }
        }

Observabilité (recommandation C4 #1) :
    --serve-metrics démarre un serveur http.server stdlib exposant /metrics au
    format texte Prometheus, lu depuis data/llm_cascade_log.jsonl. La logique
    d'agrégation est réutilisée depuis monitoring/llm_stats.py (stdlib pure).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

# --- Endpoints (mono-machine M1 ; M2/M5 DOWN gérés par le proxy) -------------
PROXY_URL = os.environ.get(
    "JARVIS_PROXY_URL", "http://127.0.0.1:18800/v1/chat/completions"
)
OLLAMA_URL = os.environ.get("JARVIS_OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
JARVIS_DIR = os.environ.get("JARVIS_DIR", os.path.expanduser("~/jarvis"))
LOG_PATH = os.path.join(JARVIS_DIR, "data", "llm_cascade_log.jsonl")

# Mode → (modèle proxy, modèle ollama direct de secours)
MODE_MODELS = {
    "auto": ("auto", "gemma3:4b"),
    "fast": ("gemma3:4b", "gemma3:4b"),
    "reason": ("deepseek-r1:7b", "deepseek-r1:7b"),
    "code": ("qwen2.5-coder:7b", "qwen2.5-coder:7b"),
}
# Modèle Ollama Cloud (gratuit, dernier recours — daemon 11434 le sert en transparent)
CLOUD_MODEL = os.environ.get("JARVIS_CLOUD_MODEL", "gpt-oss:20b-cloud")

# --- Routing déclaratif optionnel (recommandation C4 #2) ---------------------
# JSON (pas YAML) volontairement, pour rester 100 % stdlib : voir docstring.
ROUTES_PATH = os.environ.get(
    "JARVIS_ROUTES", os.path.expanduser("~/.jarvis/dispatcher_routes.json")
)


def load_routes(path: str | None = None) -> dict:
    """Charge le fichier de routes optionnel et SURCHARGE la config module.

    - Fichier absent / illisible / JSON invalide → aucun changement, renvoie {}.
      Le comportement par défaut reste donc strictement identique.
    - Présent → applique les clés connues (proxy_url, ollama_url, cloud_model,
      mode_models, quotas) sur les globals du module et renvoie le dict brut
      chargé.

    Idempotent et sûr : ne lève jamais (le routing ne doit pas empêcher un appel).
    """
    global PROXY_URL, OLLAMA_URL, CLOUD_MODEL, _quotas
    p = path if path is not None else ROUTES_PATH
    if not p or not os.path.isfile(p):
        return {}
    try:
        with open(p, encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, ValueError):
        return {}  # corrompu → on garde les défauts, jamais de crash
    if not isinstance(cfg, dict):
        return {}

    if isinstance(cfg.get("proxy_url"), str):
        PROXY_URL = cfg["proxy_url"]
    if isinstance(cfg.get("ollama_url"), str):
        OLLAMA_URL = cfg["ollama_url"]
    if isinstance(cfg.get("cloud_model"), str):
        CLOUD_MODEL = cfg["cloud_model"]

    mm = cfg.get("mode_models")
    if isinstance(mm, dict):
        for mode, pair in mm.items():
            # accepte [proxy, ollama] ou une string unique (proxy=ollama)
            if isinstance(pair, (list, tuple)) and len(pair) == 2:
                MODE_MODELS[mode] = (str(pair[0]), str(pair[1]))
            elif isinstance(pair, str):
                MODE_MODELS[mode] = (pair, pair)

    # Quotas par backend (recommandation C4 #3). Schéma:
    #   "quotas": {"proxy": {"max_calls": N, "max_chars": M}, "ollama": {...}}
    # Absent → dict vide → illimité (comportement inchangé).
    q = cfg.get("quotas")
    if isinstance(q, dict):
        _quotas = {
            str(b): {str(k): int(v) for k, v in lim.items()
                     if isinstance(v, (int, float))}
            for b, lim in q.items()
            if isinstance(lim, dict)
        }
    return cfg


# --- Quotas par backend & usage en mémoire (recommandation C4 #3) -----------
# _quotas : limites optionnelles chargées depuis dispatcher_routes.json (clé
#   "quotas"). Vide → illimité, comportement actuel strictement inchangé.
# _usage  : compteurs cumulés en mémoire {backend: {"calls": n, "chars": m}}.
_quotas: dict[str, dict] = {}
_usage: dict[str, dict] = {}


def _usage_record(backend: str, chars: int) -> None:
    """Incrémente les compteurs en mémoire pour le backend servi."""
    u = _usage.setdefault(backend, {"calls": 0, "chars": 0})
    u["calls"] += 1
    u["chars"] += max(0, int(chars))


def get_usage() -> dict:
    """Expose une copie de l'usage cumulé par backend (calls + chars)."""
    return {b: dict(v) for b, v in _usage.items()}


def _quota_exceeded(backend: str) -> bool:
    """True si le backend a atteint/dépassé une de ses limites configurées.

    Limites absentes → toujours False (illimité). On compare l'usage DÉJÀ
    consommé : un backend au quota est sauté comme un circuit ouvert.
    """
    lim = _quotas.get(backend)
    if not lim:
        return False
    u = _usage.get(backend, {"calls": 0, "chars": 0})
    if "max_calls" in lim and u["calls"] >= lim["max_calls"]:
        return True
    if "max_chars" in lim and u["chars"] >= lim["max_chars"]:
        return True
    return False


# --- Secrets : fichier protégé chmod 600 + fallback env (recommandation C4 #3)
# Aucun secret en dur. _load_secret(name) lit ~/.jarvis/secrets.json (vérifie les
# permissions, warn si trop ouvertes) puis retombe sur os.environ. Prépare le
# terrain pour des backends authentifiés sans coder de clé dans le source.
SECRETS_PATH = os.environ.get(
    "JARVIS_SECRETS", os.path.expanduser("~/.jarvis/secrets.json")
)


def _warn(msg: str) -> None:
    """Émet un avertissement non bloquant (stderr). Monkeypatchable en test."""
    print(f"[dispatcher] WARN: {msg}", file=sys.stderr)


def _load_secret(name: str) -> str | None:
    """Retourne le secret `name` depuis secrets.json (prioritaire) sinon env.

    - Fichier présent mais lisible par groupe/autres (perms != 600 strict) →
      _warn(), mais on lit quand même la valeur.
    - Fichier absent / JSON invalide / clé absente → fallback os.environ.
    - Jamais d'exception : retourne None si introuvable partout.
    """
    val = None
    try:
        if os.path.isfile(SECRETS_PATH):
            mode = os.stat(SECRETS_PATH).st_mode & 0o777
            if mode & 0o077:  # le moindre bit groupe/autres → trop permissif
                _warn(
                    f"{SECRETS_PATH} permissions {oct(mode)} trop ouvertes "
                    f"(attendu 600) — chmod 600 recommandé"
                )
            with open(SECRETS_PATH, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and name in data:
                val = data[name]
    except (OSError, ValueError):
        val = None  # fichier corrompu/illisible → on retombe sur l'env
    if val is None:
        val = os.environ.get(name)
    return val


# --- Circuit-breaker par backend --------------------------------------------
_CB_THRESHOLD = 3  # échecs consécutifs avant ouverture
_CB_COOLDOWN = 30.0  # secondes d'ouverture avant ré-essai
_circuit: dict[str, dict] = {}


def _clock() -> float:
    return time.monotonic()


def _cb_open(backend: str) -> bool:
    """True si le circuit du backend est ouvert (on saute le backend)."""
    st = _circuit.get(backend)
    if not st or st["fails"] < _CB_THRESHOLD:
        return False
    if _clock() - st["opened_at"] >= _CB_COOLDOWN:
        st["fails"] = 0  # cooldown écoulé → demi-ouverture, on retente
        return False
    return True


def _cb_record(backend: str, ok: bool) -> None:
    st = _circuit.setdefault(backend, {"fails": 0, "opened_at": 0.0})
    if ok:
        st["fails"] = 0
    else:
        st["fails"] += 1
        if st["fails"] == _CB_THRESHOLD:
            st["opened_at"] = _clock()


# --- HTTP bas niveau (stdlib, pas de dépendance dure) -----------------------
def _post_json(url: str, payload: dict, timeout: float) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _call_proxy(messages: list, model: str, timeout: float) -> tuple[str, str]:
    """Appel du proxy unifié. Retourne (texte, backend_servi)."""
    d = _post_json(
        PROXY_URL,
        {"model": model, "messages": messages, "stream": False, "max_tokens": 2048},
        timeout,
    )
    text = d["choices"][0]["message"]["content"]
    served = d.get("model") or "proxy"
    return text, served


def _call_ollama(messages: list, model: str, timeout: float) -> tuple[str, str]:
    """Fallback direct Ollama (local ou :cloud). Retourne (texte, backend)."""
    d = _post_json(
        OLLAMA_URL, {"model": model, "messages": messages, "stream": False}, timeout
    )
    return d["message"]["content"], f"ollama/{model}"


def _retry(fn, attempts: int = 3, base: float = 0.5):
    """Retry backoff exponentiel. Lève la dernière exception si tout échoue."""
    last = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 — on veut retenter sur toute erreur transitoire
            last = e
            if i < attempts - 1:
                time.sleep(base * (2**i))
    raise last


def _log(via: str, served: str, ms: int, ok: bool, tried: int, chars: int) -> None:
    """Append JSONL au format existant {ts, via, served, ms, ok, tried, chars}."""
    rec = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z",
        "via": via,
        "served": served,
        "ms": ms,
        "ok": ok,
        "tried": tried,
        "chars": chars,
    }
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(rec) + "\n")
    except OSError:
        pass  # le log est best-effort, jamais bloquant


def ask(
    prompt: str,
    *,
    mode: str = "auto",
    system: str | None = None,
    model: str | None = None,
    timeout: float = 120.0,
) -> dict:
    """Porte d'entrée unique. Retourne {text, backend, latency_ms, ok}.

    Chaîne de secours : proxy unifié → Ollama local direct → Ollama Cloud.
    Chaque maillon est protégé par circuit-breaker + retry ; jamais de SPOF total.
    """
    proxy_model, ollama_model = MODE_MODELS.get(mode, MODE_MODELS["auto"])
    if model:
        proxy_model = ollama_model = model
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": prompt}
    ]

    t0 = _clock()
    tried = 0
    # (nom_backend, via, callable) dans l'ordre de la chaîne de secours
    chain = [
        (
            "proxy",
            "dispatcher/proxy",
            lambda: _call_proxy(messages, proxy_model, timeout),
        ),
        (
            "ollama",
            "dispatcher/ollama",
            lambda: _call_ollama(messages, ollama_model, timeout),
        ),
        (
            "cloud",
            "dispatcher/cloud",
            lambda: _call_ollama(messages, CLOUD_MODEL, timeout),
        ),
    ]
    last_err = None
    for backend, via, fn in chain:
        # Sauté si circuit ouvert (panne) OU quota du backend dépassé (budget).
        if _cb_open(backend) or _quota_exceeded(backend):
            continue
        tried += 1
        try:
            text, served = _retry(fn)
            _cb_record(backend, True)
            _usage_record(backend, len(text))
            ms = int((_clock() - t0) * 1000)
            _log(via, served, ms, True, tried - 1, len(text))
            return {"text": text, "backend": served, "latency_ms": ms, "ok": True}
        except Exception as e:  # noqa: BLE001
            _cb_record(backend, False)
            last_err = e

    ms = int((_clock() - t0) * 1000)
    _log("dispatcher/failed", "none", ms, False, tried, 0)
    return {
        "text": f"⚠️ Tous les backends ont échoué : {last_err}",
        "backend": "none",
        "latency_ms": ms,
        "ok": False,
    }


# --- Embeddings (Phase 1.3 — lever le SPOF embeddings) ----------------------
EMBED_URL = os.environ.get("JARVIS_EMBED_URL", "http://127.0.0.1:11434/api/embeddings")
EMBED_MODEL = os.environ.get("JARVIS_EMBED_MODEL", "nomic-embed-text")
# Fallback embeddings : 2e endpoint Ollama (ex. LMS M1 ou Ollama Cloud). Vide = pas
# de fallback cloud gratuit garanti pour les embeddings → en mono-machine, le local
# suffit ; ce hook permet d'en brancher un sans toucher le code.
EMBED_FALLBACK_URL = os.environ.get("JARVIS_EMBED_FALLBACK_URL", "")


def embed(text: str, *, model: str | None = None, timeout: float = 60.0) -> dict:
    """Retourne {embedding, backend, ok}. Retry + circuit-breaker, fallback optionnel.
    Lève jamais : renvoie ok=False si tous les endpoints échouent."""
    mdl = model or EMBED_MODEL
    endpoints = [("embed-local", EMBED_URL)]
    if EMBED_FALLBACK_URL:
        endpoints.append(("embed-fallback", EMBED_FALLBACK_URL))
    last_err = None
    for backend, url in endpoints:
        if _cb_open(backend):
            continue
        try:
            d = _retry(lambda: _post_json(url, {"model": mdl, "prompt": text}, timeout))
            vec = d.get("embedding") or (d.get("data", [{}])[0].get("embedding"))
            if not vec:
                raise ValueError("réponse sans embedding")
            _cb_record(backend, True)
            return {"embedding": vec, "backend": backend, "ok": True}
        except Exception as e:  # noqa: BLE001
            _cb_record(backend, False)
            last_err = e
    return {"embedding": None, "backend": "none", "ok": False, "error": str(last_err)}


# --- Métriques Prometheus (recommandation C4 #1) ----------------------------
# On RÉUTILISE monitoring/llm_stats.py (stdlib pure) plutôt que de réimplémenter
# l'agrégation et le rendu Prometheus. Import paresseux + tolérant : si le module
# n'est pas trouvable (chemin exotique), on dégrade proprement.
def _load_stats_module():
    import importlib.util

    here = os.path.dirname(os.path.abspath(__file__))
    mod_path = os.path.join(here, "..", "monitoring", "llm_stats.py")
    mod_path = os.path.normpath(mod_path)
    spec = importlib.util.spec_from_file_location("jarvis_llm_stats", mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def render_metrics(log_path: str | None = None) -> str:
    """Rend le texte Prometheus depuis le JSONL de cascade (fenêtre: tout).

    Réutilise compute_stats/render_prometheus de monitoring/llm_stats.py.
    Log absent → rendu minimal valide (compteur à 0), jamais d'exception.
    """
    from pathlib import Path

    path = Path(log_path if log_path is not None else LOG_PATH)
    if not path.exists():
        return "# log absent: " + str(path) + "\njarvis_llm_requests_total 0\n"
    stats = _load_stats_module()
    # since=None → tout l'historique (cohérent avec un scrape de compteur cumulatif)
    s = stats.compute_stats(path, None)
    return stats.render_prometheus(s)


from http.server import BaseHTTPRequestHandler, HTTPServer  # noqa: E402


class _MetricsHandler(BaseHTTPRequestHandler):
    """Handler stdlib : GET /metrics → texte Prometheus. Tout le reste → 404."""

    def do_GET(self):  # noqa: N802 (nom imposé par BaseHTTPRequestHandler)
        if self.path.rstrip("/") not in ("/metrics", ""):
            self.send_response(404)
            self.end_headers()
            return
        try:
            body = render_metrics(LOG_PATH).encode("utf-8")
        except Exception as e:  # noqa: BLE001 — un scrape ne doit jamais 500 brut
            body = (f"# error: {e}\njarvis_llm_requests_total 0\n").encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # silence l'access-log stdout bruyant
        pass


def serve_metrics(port: int = 9109, host: str = "0.0.0.0") -> None:
    """Démarre le serveur /metrics (bloquant). Stdlib uniquement."""
    httpd = HTTPServer((host, port), _MetricsHandler)
    print(f"[dispatcher] /metrics sur http://{host}:{port}/metrics", file=sys.stderr)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


def _main(argv: list | None = None) -> int:
    # Routing déclaratif chargé au démarrage (no-op si fichier absent).
    load_routes()

    p = argparse.ArgumentParser(description="JARVIS dispatcher LLM unifié")
    p.add_argument("prompt", nargs="?", help="le prompt à envoyer")
    p.add_argument(
        "--mode",
        default="auto",
        help="auto (défaut) | fast | reason | code | <mode custom routes.json>",
    )
    p.add_argument("--system", default=None, help="prompt système optionnel")
    p.add_argument("--model", default=None, help="forcer un modèle précis")
    p.add_argument("--timeout", type=float, default=120.0)
    p.add_argument("--json", action="store_true", help="sortie JSON complète")
    p.add_argument(
        "--serve-metrics",
        action="store_true",
        help="démarre le serveur HTTP /metrics (Prometheus) au lieu d'un prompt",
    )
    p.add_argument(
        "--port", type=int, default=9109, help="port du serveur /metrics (défaut 9109)"
    )
    a = p.parse_args(argv)

    if a.serve_metrics:
        serve_metrics(port=a.port)
        return 0

    if not a.prompt:
        p.error("prompt requis (ou utilisez --serve-metrics)")

    r = ask(a.prompt, mode=a.mode, system=a.system, model=a.model, timeout=a.timeout)
    if a.json:
        print(json.dumps(r, ensure_ascii=False))
    else:
        print(r["text"])
        print(
            f"\n— {r['backend']} · {r['latency_ms']}ms · ok={r['ok']}", file=sys.stderr
        )
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(_main())
