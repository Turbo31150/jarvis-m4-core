#!/usr/bin/env python3
"""Moteur IA adaptatif pour l'Espace Prof — s'adapte à l'environnement.

Cascade ANTI-SURCHAUFFE (déporté d'abord, local en dernier recours, 0 token) :
  1. Cache SQL (ecole.db: ai_cache) → instantané, 0 watt, 0 chaleur
  2. Cluster LM Studio M1/M2 (qwen3.5-35b, distillations Claude) — DÉPORTÉ, si joignable
  3. Ollama cloud (kimi-k2.5:cloud) — DÉPORTÉ, si `ollama signin` fait
  4. Gemini / Antigravity (gemini-smart.sh) — DÉPORTÉ Google One
  5. Ollama local CPU (gemma3:4b/qwen2.5:7b) — DERNIER RECOURS, BLOQUÉ si M4 ≥ LOCAL_MAX_TEMP
Règle d'or : le local CPU chauffe le M4 (plafond 95°C). On ne l'allume que si la
température est sous le seuil du gouverneur. Sinon → AIUnavailable (app utilisable en manuel).
"""

import hashlib
import json
import os
import sqlite3
import subprocess
from pathlib import Path

import requests

ECOLE_DB = Path(__file__).resolve().parent / "ecole.db"
M1 = "http://192.168.1.85:1234"
M2 = "http://192.168.1.26:1234"
OLLAMA = "http://127.0.0.1:11434"
GEMINI_SH = str(Path.home() / "jarvis" / "scripts" / "gemini-ask.sh")
# --- Ollama CLOUD (déporté, 0 chaleur sur le M4) ---
OLLAMA_CLOUD_HOST = "https://ollama.com"  # API directe (mode clé)
OLLAMA_CLOUD_MODEL = os.environ.get("OLLAMA_CLOUD_MODEL", "gpt-oss:120b")
OLLAMA_API_KEY = os.environ.get(
    "OLLAMA_API_KEY", ""
)  # créer sur ollama.com/settings/keys
# --- Z.AI GLM Coding Plan (déporté, qualité ; clé sur z.ai/manage-apikey) ---
ZAI_BASE = os.environ.get("ZAI_BASE", "https://api.z.ai/api/paas/v4")
ZAI_MODEL = os.environ.get("ZAI_MODEL", "glm-4.6")  # ex glm-5.2 / glm-4.6
ZAI_API_KEY = os.environ.get("ZAI_API_KEY", "")
LOCAL_MAX_TEMP = (
    82  # °C : au-delà, on REFUSE l'inférence locale CPU (anti-emballement M4)
)


class AIUnavailable(Exception):
    pass


def _gpu_temp():
    """Température la plus CHAUDE du M4 (CPU package OU GPU), en °C.
    nvidia-smi seul sous-estime (ne voit que la dGPU) : l'inférence CPU chauffe le
    package, lu via /sys/class/thermal. On renvoie le max des deux → garde-fou fiable."""
    temps = []
    try:
        out = (
            subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=temperature.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=4,
            )
            .stdout.strip()
            .splitlines()
        )
        if out:
            temps.append(int(out[0]))
    except Exception:
        pass
    try:
        import glob

        for zone in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
            try:
                with open(zone) as f:
                    temps.append(int(f.read().strip()) // 1000)
            except Exception:
                continue
    except Exception:
        pass
    return max(temps) if temps else 0


_UP_CACHE = {}  # url -> (timestamp, ok) ; évite de re-sonder un nœud down à chaque appel
_UP_TTL = 15.0


def _up(url, timeout=1.5):
    import time

    now = time.time()
    hit = _UP_CACHE.get(url)
    if hit and now - hit[0] < _UP_TTL:
        return hit[1]
    ok = False
    try:
        ok = requests.get(f"{url}/v1/models", timeout=timeout).ok
    except requests.exceptions.RequestException as e:
        # Hôte injoignable (timeout de connexion / refus) → re-sonder le MÊME hôte mort
        # est inutile et double le coût (2 nœuds down = dashboard figé). On ne tente le
        # second endpoint (API Ollama) que si l'hôte a répondu mais pas sur /v1/models.
        unreachable = isinstance(
            e, (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError)
        )
        if not unreachable:
            try:
                ok = requests.get(f"{url}/api/tags", timeout=timeout).ok
            except requests.exceptions.RequestException:
                ok = False
    _UP_CACHE[url] = (now, ok)
    return ok


def _cache_get(key):
    try:
        with sqlite3.connect(str(ECOLE_DB)) as c:
            r = c.execute("SELECT answer FROM ai_cache WHERE key=?", (key,)).fetchone()
            if r:
                c.execute("UPDATE ai_cache SET hits=hits+1 WHERE key=?", (key,))
                return r[0]
    except Exception:
        pass
    return None


def _cache_put(key, q, a, backend):
    try:
        with sqlite3.connect(str(ECOLE_DB)) as c:
            c.execute(
                "INSERT OR REPLACE INTO ai_cache(key,question,answer,backend,hits) "
                "VALUES(?,?,?,?,0)",
                (key, q[:500], a, backend),
            )
    except Exception:
        pass


def _gemini(prompt, timeout=180):
    """Filet de sécurité : Gemini via gemini-ask.sh (Google One, 0 token facturé).
    N'est appelé qu'en dernier recours (cluster + Ollama KO). Renvoie le texte ou None."""
    try:
        r = subprocess.run(
            ["bash", GEMINI_SH, prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        txt = (r.stdout or "").strip()
        return txt or None
    except Exception:
        return None


def _zai(msgs, max_tokens, temperature):
    """Z.AI GLM Coding Plan — DÉPORTÉ (forfait plat), 0 chaleur M4. Texte ou None.
    Endpoint OpenAI-compatible. Nécessite ZAI_API_KEY."""
    if not ZAI_API_KEY:
        return None
    try:
        r = requests.post(
            f"{ZAI_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {ZAI_API_KEY}"},
            json={
                "model": ZAI_MODEL,
                "messages": msgs,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=120,
        )
        txt = r.json()["choices"][0]["message"]["content"].strip()
        return txt or None
    except Exception:
        return None


def _ollama_cloud(msgs, max_tokens, temperature):
    """Ollama CLOUD — DÉPORTÉ, 0 chaleur, 0 token. Renvoie le texte ou None.
    Mode 1 (préféré) : API directe ollama.com via OLLAMA_API_KEY — ne dépend pas du
                       daemon local, donc marche même daemon éteint.
    Mode 2 (repli)   : offload via daemon local signé (`ollama signin`), modèle -cloud.
    """
    # Mode 1 — API directe par clé
    if OLLAMA_API_KEY:
        try:
            r = requests.post(
                f"{OLLAMA_CLOUD_HOST}/api/chat",
                headers={"Authorization": f"Bearer {OLLAMA_API_KEY}"},
                json={
                    "model": OLLAMA_CLOUD_MODEL,
                    "messages": msgs,
                    "stream": False,
                    "options": {"num_predict": max_tokens, "temperature": temperature},
                },
                timeout=120,
            )
            txt = r.json().get("message", {}).get("content", "").strip()
            if txt:
                return txt
        except Exception:
            pass
    # Mode 2 — offload via daemon local signé (suffixe -cloud requis)
    if _up(OLLAMA):
        model = (
            OLLAMA_CLOUD_MODEL
            if OLLAMA_CLOUD_MODEL.endswith("-cloud")
            else OLLAMA_CLOUD_MODEL + "-cloud"
        )
        try:
            r = requests.post(
                f"{OLLAMA}/api/chat",
                json={
                    "model": model,
                    "messages": msgs,
                    "stream": False,
                    "think": False,
                    "options": {"num_predict": max_tokens, "temperature": temperature},
                },
                timeout=120,
            )
            j = r.json()
            if "sign" not in (j.get("error") or "").lower():
                txt = j.get("message", {}).get("content", "").strip()
                if txt:
                    return txt
        except Exception:
            pass
    return None


def _ollama_cloud_ready():
    """True si Ollama cloud est utilisable : clé API définie OU daemon avec modèle -cloud."""
    if OLLAMA_API_KEY:
        return True
    try:
        r = requests.get(f"{OLLAMA}/api/tags", timeout=2)
        names = [m.get("name", "") for m in r.json().get("models", [])]
        return any(n.endswith("-cloud") or ":cloud" in n for n in names)
    except Exception:
        return False


def backend_status():
    """État de l'environnement (pour l'UI). temp = point le plus chaud du M4.

    Les sondes réseau (nœuds cluster + ollama) tournent EN PARALLÈLE : sondées en
    série, deux nœuds down bloquaient le dashboard ~8 s à froid (cf. _UP_CACHE TTL).
    """
    from concurrent.futures import ThreadPoolExecutor

    temp = _gpu_temp()
    with ThreadPoolExecutor(max_workers=4) as ex:
        f_m1 = ex.submit(_up, M1)
        f_m2 = ex.submit(_up, M2)
        f_ol = ex.submit(_up, OLLAMA)
        f_cloud = ex.submit(_ollama_cloud_ready)
        m1, m2, ol, cloud = (
            f_m1.result(),
            f_m2.result(),
            f_ol.result(),
            f_cloud.result(),
        )
    return {
        "cluster_m1": m1,
        "cluster_m2": m2,
        "ollama_local": ol,
        "ollama_cloud": cloud,
        "gpu_temp": temp,
        "local_bride": temp
        >= LOCAL_MAX_TEMP,  # True = inférence locale refusée (trop chaud)
        "seuil_local": LOCAL_MAX_TEMP,
    }


def generate(
    user,
    system="Tu es un assistant pédagogique pour une enseignante du primaire en France. Réponds en français, clair, bienveillant, prêt à l'emploi.",
    max_tokens=1500,
    cache=True,
    temperature=0.5,
):
    key = hashlib.sha256((system + "||" + user).encode()).hexdigest()[:40]
    if cache:
        hit = _cache_get(key)
        if hit:
            return {"text": hit, "backend": "cache", "cached": True}

    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]

    # ═══ DÉPORTÉ D'ABORD (0 chaleur sur le M4) ═══

    # 1) Cluster LM Studio M1/M2 (meilleure qualité, distillations Claude) si joignable
    for node, url in (("M1", M1), ("M2", M2)):
        if not _up(url):
            continue
        try:
            r = requests.post(
                f"{url}/v1/chat/completions",
                json={
                    "model": "qwen3.5-35b-a3b",
                    "messages": msgs,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=120,
            )
            txt = r.json()["choices"][0]["message"]["content"].strip()
            if txt:
                if cache:
                    _cache_put(key, user, txt, node)
                return {"text": txt, "backend": node, "cached": False}
        except Exception:
            continue

    # 2) Z.AI GLM Coding Plan — DÉPORTÉ (qualité), si clé ZAI_API_KEY définie.
    txt = _zai(msgs, max_tokens, temperature)
    if txt:
        if cache:
            _cache_put(key, user, txt, f"zai:{ZAI_MODEL}")
        return {"text": txt, "backend": f"zai:{ZAI_MODEL}", "cached": False}

    # 3) Ollama CLOUD — DÉPORTÉ (API directe par clé, ou offload daemon signé).
    txt = _ollama_cloud(msgs, max_tokens, temperature)
    if txt:
        if cache:
            _cache_put(key, user, txt, "ollama-cloud")
        return {"text": txt, "backend": "ollama-cloud", "cached": False}

    # 3) Gemini / Antigravity (Google One, 0 token) — déporté, via gemini-smart.sh
    g = _gemini(f"{system}\n\n{user}")
    if g:
        if cache:
            _cache_put(key, user, g, "gemini")
        return {"text": g, "backend": "gemini", "cached": False}

    # ═══ LOCAL EN TOUT DERNIER RECOURS — chauffe le M4, BLOQUÉ si trop chaud ═══
    temp = _gpu_temp()
    if _up(OLLAMA) and temp < LOCAL_MAX_TEMP:
        for model in ("gemma3:4b", "qwen2.5:7b"):
            try:
                r = requests.post(
                    f"{OLLAMA}/api/chat",
                    json={
                        "model": model,
                        "messages": msgs,
                        "stream": False,
                        "think": False,
                        "options": {
                            "num_predict": max_tokens,
                            "temperature": temperature,
                            "num_gpu": 0,  # CPU forcé : VRAM 4 Go occupée par Whisper
                        },
                    },
                    timeout=240,
                )
                txt = r.json().get("message", {}).get("content", "").strip()
                if txt:
                    if cache:
                        _cache_put(key, user, txt, f"ollama-local:{model}")
                    return {
                        "text": txt,
                        "backend": f"ollama-local:{model}",
                        "cached": False,
                    }
            except Exception:
                continue

    if temp >= LOCAL_MAX_TEMP:
        raise AIUnavailable(
            f"Backends déportés KO (cluster down, Ollama cloud non connecté, Gemini KO) "
            f"et inférence locale BLOQUÉE : M4 à {temp}°C ≥ {LOCAL_MAX_TEMP}°C "
            f"(anti-surchauffe). Connecte un backend déporté : `ollama signin`, "
            f"allume M1/M2, ou migre Gemini→Antigravity."
        )
    raise AIUnavailable(
        "Aucun moteur IA disponible (cluster, Ollama cloud, Gemini, Ollama local tous KO)."
    )


if __name__ == "__main__":
    import sys

    print("env:", json.dumps(backend_status(), ensure_ascii=False))
    if len(sys.argv) > 1:
        res = generate(" ".join(sys.argv[1:]))
        print(f"\n[{res['backend']}]\n{res['text']}")
