#!/usr/bin/env python3
"""
JARVIS Keyword Router
Surveille ~/jarvis/subtitles/live.txt, détecte le thème, appelle le bon LLM.
"""

import json
import hashlib
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

# ── Chemins ──────────────────────────────────────────────────────────────────
BASE_DIR = Path.home() / "jarvis" / "multiagent"
KEYWORDS_FILE = BASE_DIR / "keywords.json"
OUTPUT_DIR = BASE_DIR / "output"
LOG_FILE = BASE_DIR / "router.log"
LIVE_TXT = Path.home() / "jarvis" / "subtitles" / "live.txt"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("jarvis-router")

# ── Config ────────────────────────────────────────────────────────────────────
POLL_INTERVAL = 0.5  # secondes
TIMEOUT = 30  # secondes par requête API


def load_keywords():
    with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def detect_theme(text: str, config: dict) -> str:
    """Retourne le nom du thème dont le plus grand nombre de mots-clés matchent."""
    text_lower = text.lower()
    themes = config["themes"]
    default = config.get("default_theme", "général")

    scores = {}
    for theme, data in themes.items():
        if theme == default:
            continue
        score = sum(1 for kw in data["keywords"] if kw in text_lower)
        if score > 0:
            scores[theme] = score

    if not scores:
        return default
    return max(scores, key=scores.get)


def build_openai_payload(system_prompt: str, user_text: str, model_id: str) -> dict:
    return {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.7,
        "max_tokens": 512,
    }


def call_lmstudio(url: str, payload: dict) -> str:
    """Appelle une API compatible OpenAI (LM Studio). Retourne le texte ou lève une exception."""
    endpoint = url.rstrip("/") + "/v1/chat/completions"
    resp = requests.post(endpoint, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def call_ollama(text: str, system_prompt: str, model: str) -> str:
    """Fallback Ollama via /api/chat."""
    endpoint = "http://127.0.0.1:11434/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        "stream": False,
    }
    resp = requests.post(endpoint, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()


def route_and_call(text: str, config: dict) -> tuple[str, str, str]:
    """
    Détecte le thème, tente la chaîne de fallback.
    Retourne (theme, response, backend_used).
    """
    theme = detect_theme(text, config)
    theme_cfg = config["themes"][theme]
    system_prompt = theme_cfg["system_prompt"]
    model_id = theme_cfg["model_id"]
    primary_url = theme_cfg["model_url"]
    fallback_chain = config.get("fallback_chain", [])
    ollama_model = config.get("ollama_model", "gemma3:4b")

    # Construire la liste d'URLs à essayer (primary en premier, puis fallback sans doublon)
    urls_to_try = [primary_url]
    for fb_url in fallback_chain:
        if fb_url != primary_url and "11434" not in fb_url:
            urls_to_try.append(fb_url)

    payload = build_openai_payload(system_prompt, text, model_id)

    for url in urls_to_try:
        try:
            log.info(f"[{theme}] Essai {url} …")
            response = call_lmstudio(url, payload)
            return theme, response, url
        except Exception as e:
            log.warning(f"[{theme}] {url} KO : {e}")

    # Dernier recours : Ollama local
    try:
        log.info(f"[{theme}] Fallback Ollama ({ollama_model}) …")
        response = call_ollama(text, system_prompt, ollama_model)
        return theme, response, "ollama:11434"
    except Exception as e:
        log.error(f"[{theme}] Ollama KO : {e}")
        return theme, f"[ERREUR] Tous les backends sont down : {e}", "none"


def write_output(theme: str, query: str, response: str, backend: str):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = OUTPUT_DIR / f"{ts}_{theme}.txt"
    content = (
        f"=== JARVIS ROUTER — {ts} ===\n"
        f"THEME   : {theme}\n"
        f"BACKEND : {backend}\n"
        f"QUERY   :\n{query}\n\n"
        f"RESPONSE:\n{response}\n"
    )
    filename.write_text(content, encoding="utf-8")
    log.info(f"Output → {filename.name}")


def text_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def read_live(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def main():
    log.info("JARVIS Router démarré. Surveillance de %s", LIVE_TXT)

    if not KEYWORDS_FILE.exists():
        log.error("keywords.json introuvable : %s", KEYWORDS_FILE)
        sys.exit(1)

    config = load_keywords()
    last_hash = ""

    while True:
        try:
            text = read_live(LIVE_TXT)
            if not text:
                time.sleep(POLL_INTERVAL)
                continue

            h = text_hash(text)
            if h == last_hash:
                time.sleep(POLL_INTERVAL)
                continue

            last_hash = h
            log.info(f"Nouveau texte détecté ({len(text)} chars)")

            # Recharger la config à chaque itération (permet hot-reload)
            config = load_keywords()

            theme, response, backend = route_and_call(text, config)
            write_output(theme, text, response, backend)

        except KeyboardInterrupt:
            log.info("Arrêt demandé.")
            break
        except Exception as e:
            log.error(f"Erreur boucle principale : {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
