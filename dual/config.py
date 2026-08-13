"""Configuration centralisée + auto-découverte des backends réellement présents.

Ordre de résolution : variables d'environnement > dual/config.json > découverte.
Aucune URL n'est codée en dur ailleurs dans le projet.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = Path(os.environ.get("JARVIS_DUAL_CONFIG", ROOT / "dual" / "config.json"))
LOG_DIR = Path(os.environ.get("JARVIS_DUAL_LOGS", ROOT / "logs" / "dual"))
JOB_DIR = Path(os.environ.get("JARVIS_DUAL_JOBS", ROOT / "data" / "dual-jobs"))

# Candidats testés à la découverte (aucun n'est supposé actif).
CANDIDATES = [
    ("lmstudio", "http://127.0.0.1:1234"),
    ("ollama", "http://127.0.0.1:11434"),
    ("lmstudio_m6", "http://10.42.0.1:1234"),
    ("lmstudio_m1", "http://192.168.0.250:1234"),
    # Worker CLI : pas d'URL, mais un binaire authentifié dans le PATH.
    ("agy", "cli://agy"),
]

DEFAULTS = {
    "timeouts": {"connect": 5.0, "first_token": 60.0, "idle": 30.0, "request": 300.0},
    "retry": {"max_attempts": 3, "backoff_base_s": 1.5},
    "workers": {},
    "providers": {},
}


def load() -> dict:
    cfg = json.loads(json.dumps(DEFAULTS))
    if CONFIG_PATH.exists():
        try:
            cfg.update(json.loads(CONFIG_PATH.read_text()))
        except json.JSONDecodeError as e:
            raise SystemExit(f"config.json illisible: {e}")
    # surcharge env
    for env, path in (
        ("LMSTUDIO_BASE_URL", ("providers", "lmstudio", "base_url")),
        ("OLLAMA_BASE_URL", ("providers", "ollama", "base_url")),
    ):
        v = os.environ.get(env)
        if v:
            cfg.setdefault(path[0], {}).setdefault(path[1], {})[path[2]] = v
    for env, key in (("JARVIS_WORKER_A", "worker_a"), ("JARVIS_WORKER_B", "worker_b")):
        v = os.environ.get(env)
        if v and key in cfg.get("workers", {}):
            cfg["workers"][key]["model"] = v
    return cfg


def resolve(force_discover: bool = False) -> dict:
    """Config effective : le fichier vérifié prime sur une redécouverte.

    Une redécouverte non sondée reclasserait les modèles par simple préférence
    de nom et pourrait réélire un modèle fantôme écarté par `discover --probe`.
    Le travail de vérification déjà payé ne doit pas être jeté à chaque commande.
    """
    cfg = load()
    if not force_discover and cfg.get("workers") and cfg.get("providers"):
        cfg["source"] = str(CONFIG_PATH)
        return cfg
    cfg = discover()
    cfg["source"] = "découverte à chaud"
    return cfg


def save(cfg: dict) -> Path:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
    return CONFIG_PATH


def discover(
    verbose: bool = False, probe: bool = False, probe_tokens: int = 300
) -> dict:
    """Sonde réellement chaque candidat et construit une config vérifiée.

    `probe=True` va plus loin : il exige une INFÉRENCE réussie pour retenir un
    modèle. Un serveur peut lister des modèles qu'il ne sait pas charger
    (constat : LM Studio :1234 liste 4 modèles et n'en charge aucun) — la seule
    preuve acceptable est une réponse non vide.
    """
    from .providers import Timeouts, build_provider  # noqa: F401 (utilisé si probe)

    cfg = load()
    providers, found = {}, []
    for alias, url in CANDIDATES:
        kind = ("agy" if alias == "agy"
                else "ollama" if alias.startswith("ollama")
                else "lmstudio")
        try:
            p = build_provider(kind, url)
            models = p.discover_models()
        except Exception as e:  # noqa: BLE001 - un backend absent est normal
            if verbose:
                print(f"  [--] {alias:14s} {url:28s} {type(e).__name__}")
            continue
        if not models:
            continue
        usable = models
        if probe:
            t = Timeouts(connect=5, first_token=180, idle=60, request=300)
            pr = build_provider(kind, url, t)
            usable = []
            for m in models:
                if "embed" in m.lower():
                    continue
                r = pr.chat(
                    m,
                    [{"role": "user", "content": "Dis simplement: OK"}],
                    max_tokens=probe_tokens,
                    temperature=0,
                )
                if verbose:
                    print(f"       probe {m:38s} {r.status}")
                if r.ok:
                    usable.append(m)
            if not usable:
                if verbose:
                    print(
                        f"  [!!] {alias:14s} {url:28s} liste des modèles mais "
                        f"aucun ne répond → écarté"
                    )
                continue

        providers[alias] = {
            "kind": kind,
            "base_url": url,
            "models": usable,
            "probed": probe,
        }
        found.append((alias, usable))
        if verbose:
            print(f"  [OK] {alias:14s} {url:28s} {len(usable)} modèle(s) utilisable(s)")

    cfg["providers"] = providers
    cfg["workers"] = _assign_workers(found)
    return cfg


def _assign_workers(found: list[tuple[str, list[str]]]) -> dict:
    """A et B doivent viser des BACKENDS DISTINCTS : deux modèles sur un même
    serveur mono-GPU sérialisent l'inférence (constat matériel M4, 4 Go VRAM).
    """
    workers = {}
    prefer = {
        "lmstudio": ["qwen/qwen3.5-9b", "qwen/qwen2.5-coder-14b"],
        # M6 : deepseek répond réellement, qwen3.5-9b consomme tout son budget
        # en raisonnement et renvoie un contenu vide (mesuré le 13/08/2026).
        "lmstudio_m6": ["deepseek/deepseek-r1-0528-qwen3-8b", "qwen/qwen3.5-9b"],
        "lmstudio_m1": ["qwen/qwen3.5-9b"],
        "ollama": ["gemma3:4b", "llama3.2", "qwen2.5:1.5b", "qwen2.5:0.5b"],
        # agy : Flash low = le plus rapide, suffisant pour un worker.
        "agy": ["gemini-3.7-flash-low", "gemini-3.6-flash-low",
                "gpt-oss-120b-medium"],
    }

    def pick(alias, models):
        for m in prefer.get(alias, []):
            if m in models:
                return m
        real = [m for m in models if "embed" not in m.lower()]
        return real[0] if real else models[0]

    for slot, (alias, models) in zip(("worker_a", "worker_b"), found):
        workers[slot] = {
            "provider": alias,
            "model": pick(alias, models),
            "role": "primary" if slot == "worker_a" else "secondary",
        }
    return workers
