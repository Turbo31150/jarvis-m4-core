#!/usr/bin/env python3
"""Moteur IA adaptatif pour l'Espace Prof — s'adapte à l'environnement.

Cascade ANTI-SURCHAUFFE (déporté d'abord, local en dernier recours, 0 token) :
  1. Cache SQL (ecole.db: ai_cache) → instantané, 0 watt, 0 chaleur
  2. LM Studio M6 (câble direct, dual GPU) puis Rémi (Tailscale) — DÉPORTÉ, par défaut
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
# Parc réel 2026-08-14 : M4 (ici) + M6 (câble direct) + Rémi (Tailscale). Rien d'autre.
# M6 = LM Studio 24/7, dual GPU → backend par défaut de toute inférence.
M6 = os.environ.get("M6_HOST", "http://10.42.0.230:1234")
REMI = os.environ.get("REMI_HOST", "http://100.113.121.61:11434")
# Modèle de référence par nœud, utilisé quand aucun n'est encore résident.
# Mesuré le 2026-08-14 : sur M6, qwen2.5-coder-14b avorte au démarrage moteur
# ("Engine protocol startup was aborted") ; qwen3.5-9b charge et répond.
PREFERRED_MODEL = {
    M6: os.environ.get("M6_MODEL", "qwen/qwen3.5-9b"),
}
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
# --- Google Gemini (déporté, qualité, quota gratuit ; clé Google AI Studio) ---
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
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


_MODEL_CACHE = {}  # url -> (ts, model_id) : évite de re-lister /v1/models à chaque appel


def _pick_chat_model(url, timeout=10):
    """Renvoie l'id du 1er modèle de chat chargé sur ce nœud LM Studio.

    /v1/models liste AUSSI les modèles seulement présents sur disque : demander
    l'un d'eux déclenche un chargement JIT qui échoue ("Engine protocol startup
    was aborted") et fait tomber toute la cascade sur le cloud. On lit donc
    /api/v0/models (propre à LM Studio), qui expose `state`, pour privilégier le
    modèle résident ; on retombe sur /v1/models pour les nœuds qui ne l'exposent
    pas (Ollama). Cache 60 s. Renvoie None si rien d'exploitable.
    """
    import time

    now = time.time()
    hit = _MODEL_CACHE.get(url)
    if hit and now - hit[0] < 60:
        return hit[1]
    model = None
    data = []
    is_lmstudio = False
    try:
        data = (
            requests.get(f"{url}/api/v0/models", timeout=timeout).json().get("data", [])
        )
        is_lmstudio = True
    except (requests.exceptions.RequestException, ValueError):
        data = []
    if is_lmstudio and not any(
        m.get("state") == "loaded"
        and m.get("type") != "embeddings"
        and "embed" not in (m.get("id") or "").lower()
        for m in data
    ):
        # Nœud LM Studio sans modèle de chat résident. Le chargement JIT échoue
        # sur ce parc (« Model is unloaded », « Engine protocol startup was
        # aborted ») : insister ferait pendre l'appelant 120 s par requête avant
        # le repli. On rend la main tout de suite ; le nœud revient de lui-même
        # dès qu'un `lms load` a été fait.
        _MODEL_CACHE[url] = (now, None)
        return None
    try:
        if not data:
            data = (
                requests.get(f"{url}/v1/models", timeout=timeout).json().get("data", [])
            )
        cands = [
            m.get("id", "")
            for m in data
            if m.get("id")
            and "embed" not in m["id"].lower()
            and m.get("type") != "embeddings"
        ]
        # Un modèle résident bat toute autre préférence : lui seul répond sans
        # chargement JIT. Ensuite le modèle de référence du nœud (mesuré : sur M6,
        # qwen3.5-9b est le seul qui charge — le 14b avorte au démarrage moteur).
        # Le caractère « thinking » n'est plus qu'un départage : le bloc
        # <think></think> posé à l'appel neutralise le reasoning-runaway.
        resident = {
            m.get("id") for m in data if m.get("state") == "loaded" and m.get("id")
        }
        ref = PREFERRED_MODEL.get(url, "")
        THINKY = ("qwen3", "qwq", "deepseek-r1", "-r1")

        def _score(mid):
            return (
                0 if mid in resident else 1,
                0 if ref and mid == ref else 1,
                1 if any(t in mid.lower() for t in THINKY) else 0,
            )

        cands.sort(key=_score)
        model = cands[0] if cands else None
    except requests.exceptions.RequestException:
        model = None
    _MODEL_CACHE[url] = (now, model)
    return model


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


def _gemini(msgs, max_tokens, temperature):
    """Google Gemini — DÉPORTÉ, quota gratuit, 0 chaleur M4. Texte ou None.
    Remplace l'ancien gemini-ask.sh (cassé). Nécessite GEMINI_API_KEY."""
    if not GEMINI_API_KEY:
        return None
    # Concatène system+user en un seul prompt (API generateContent)
    prompt = "\n\n".join(m["content"] for m in msgs if m.get("content"))
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
            params={"key": GEMINI_API_KEY},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                },
            },
            timeout=60,
        )
        data = r.json()
        txt = data["candidates"][0]["content"]["parts"][0]["text"].strip()
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
        f_m6 = ex.submit(_up, M6)
        f_remi = ex.submit(_up, REMI)
        f_ol = ex.submit(_up, OLLAMA)
        f_cloud = ex.submit(_ollama_cloud_ready)
        m1, m2, ol, cloud = (
            f_m6.result(),
            f_remi.result(),
            f_ol.result(),
            f_cloud.result(),
        )
    return {
        "cluster_m6": m1,
        "cluster_remi": m2,
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
    repli=True,  # défaut : jamais de 503 (trame hors-ligne). Le dispatch passe repli=False.
    nominatif=False,  # True dès que le prompt contient un élève/une famille — voir ci-dessous
):
    """Génère un texte via la cascade 0-token.

    nominatif=True est OBLIGATOIRE dès que `user` contient un nom d'élève, une
    appréciation, une observation ou tout élément rattachable à un enfant.
    Effets, non négociables (cf. CLAUDE.md du profil ecole) :
      - les backends HORS FOYER sont sautés : Z.AI, Google Gemini, Ollama Cloud ;
        seuls M6 (câble direct, foyer) et Ollama local restent candidats ;
      - le cache est désactivé, sinon une réponse nominative devient relisible
        par une autre requête via le cache partagé `ecole.db:ai_cache`.

    Attention : `cache=False` seul ne protège PAS — il empêche de stocker, pas
    d'envoyer. Seul `nominatif=True` empêche la sortie hors du foyer.
    """
    if nominatif:
        cache = False

    key = hashlib.sha256((system + "||" + user).encode()).hexdigest()[:40]
    if cache:
        hit = _cache_get(key)
        if hit:
            return {"text": hit, "backend": "cache", "cached": True}

    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]

    # ═══ DÉPORTÉ D'ABORD (0 chaleur sur le M4) ═══

    # 1) LM Studio M6 (câble direct, dual GPU) — backend par défaut. Rémi en secours,
    #    mais c'est une machine TIERS : sautée si nominatif.
    for node, url in (("M6", M6),) + (() if nominatif else (("REMI", REMI),)):
        if not _up(url):
            continue
        model = _pick_chat_model(url)  # modèle réellement chargé sur ce nœud
        if not model:
            continue
        # Modèle « thinking » (qwen3.x, deepseek-r1) : sans bloc <think> pré-fermé,
        # tout le budget part en raisonnement et `content` revient vide.
        thinky = any(t in model.lower() for t in ("qwen3", "qwq", "deepseek-r1", "-r1"))
        node_msgs = (
            msgs
            if not thinky
            else msgs[:-1] + [{"role": "user", "content": "<think></think>" + user}]
        )
        try:
            r = requests.post(
                f"{url}/v1/chat/completions",
                json={
                    "model": model,
                    "messages": node_msgs,
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

    # ═══ BACKENDS HORS FOYER — sautés en mode nominatif (RGPD, données élèves) ═══
    if not nominatif:
        # 2) Z.AI GLM Coding Plan — DÉPORTÉ (qualité), si clé ZAI_API_KEY définie.
        txt = _zai(msgs, max_tokens, temperature)
        if txt:
            if cache:
                _cache_put(key, user, txt, f"zai:{ZAI_MODEL}")
            return {"text": txt, "backend": f"zai:{ZAI_MODEL}", "cached": False}

        # 2bis) Google Gemini — DÉPORTÉ (quota gratuit, qualité), si GEMINI_API_KEY.
        txt = _gemini(msgs, max_tokens, temperature)
        if txt:
            if cache:
                _cache_put(key, user, txt, f"gemini:{GEMINI_MODEL}")
            return {"text": txt, "backend": f"gemini:{GEMINI_MODEL}", "cached": False}

        # 3) Ollama CLOUD — DÉPORTÉ (API directe par clé, ou offload daemon signé).
        txt = _ollama_cloud(msgs, max_tokens, temperature)
        if txt:
            if cache:
                _cache_put(key, user, txt, "ollama-cloud")
            return {"text": txt, "backend": "ollama-cloud", "cached": False}

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

    # Filet HORS-IA : jamais de 503 pour les appels qui l'acceptent (repli=True).
    # Le dispatch de masse garde repli=False → AIUnavailable → retry (vraies fiches).
    if repli:
        import templates_repli

        return {
            "text": templates_repli.repli(user, system),
            "backend": "templates-local",
            "cached": False,
        }

    if temp >= LOCAL_MAX_TEMP:
        raise AIUnavailable(
            f"Backends déportés KO (cluster down, Ollama cloud non connecté, Gemini KO) "
            f"et inférence locale BLOQUÉE : M4 à {temp}°C ≥ {LOCAL_MAX_TEMP}°C "
            f"(anti-surchauffe). Connecte un backend déporté : `ollama signin`, "
            f"allume LM Studio sur M6, ou migre Gemini→Antigravity."
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
