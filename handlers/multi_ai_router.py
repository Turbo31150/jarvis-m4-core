#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
multi_ai_router — Handler jarvis-turbo
Routeur multi-IA à cascade failover sur endpoints OpenAI-compatibles GRATUITS.

Principe (aligné pattern JARVIS M3->OL1->M1->M2->GEMINI->CLAUDE) :
  1. Découverte dynamique du catalogue live via /v1/models (jamais hardcodé)
  2. Ping-test latence + dispo par provider
  3. Cascade : essaie provider par priorité, bascule au suivant si échec/lenteur
  4. JSON out strict, stdlib only (0 pip), argparse --once, __main__ guard

Voie WEB (ChatGPT/Perplexity/Claude web/Antigravity/Manus) : hors scope API,
gérée par le Dual Browser MCP. Ce handler = voie API uniquement.

Clés via env : GROQ_API_KEY, CEREBRAS_API_KEY, GEMINI_API_KEY,
MISTRAL_API_KEY, OPENROUTER_API_KEY
"""

import argparse
import json
import os
import time
import urllib.error
import urllib.request

# --- Registre providers : base_url OpenAI-compatible + env clé + poids (priorité) ---
# Poids façon dispatch vectoriel : plus haut = priorité cascade.
PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "env_key": "GROQ_API_KEY",
        "weight": 1.3,  # le + rapide (LPU ~320 tok/s)
        "note": "vitesse",
    },
    "cerebras": {
        "base_url": "https://api.cerebras.ai/v1",
        "env_key": "CEREBRAS_API_KEY",
        "weight": 1.1,  # gros volume/jour
        "note": "volume",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "env_key": "GEMINI_API_KEY",
        "weight": 1.0,  # couche compat OpenAI officielle
        "note": "contexte 1M",
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "env_key": "MISTRAL_API_KEY",
        "weight": 0.9,
        "note": "experiment tier",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "env_key": "OPENROUTER_API_KEY",
        "weight": 0.7,  # filet de sécurité, catalogue :free rotatif
        "note": "failover catalogue :free",
    },
}

TIMEOUT = 20


def _key(pcfg):
    return os.environ.get(pcfg["env_key"], "").strip()


def _req(url, headers, payload=None, method="GET"):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read().decode("utf-8", "replace")
            return {
                "ok": True,
                "status": r.status,
                "latency_ms": round((time.time() - t0) * 1000),
                "body": body,
            }
    except urllib.error.HTTPError as e:
        return {
            "ok": False,
            "status": e.code,
            "latency_ms": round((time.time() - t0) * 1000),
            "error": e.read().decode("utf-8", "replace")[:400],
        }
    except Exception as e:  # noqa
        return {
            "ok": False,
            "status": None,
            "latency_ms": round((time.time() - t0) * 1000),
            "error": str(e)[:400],
        }


def _headers(pcfg):
    return {"Authorization": "Bearer " + _key(pcfg), "Content-Type": "application/json"}


# Modèles à écarter du choix automatique : non conversationnels ou dépréciés.
# Le catalogue live donne la disponibilité, pas la pertinence — il faut trier.
EXCLUS = (
    "tts",
    "embedding",
    "image",
    "vision",
    "whisper",
    "guard",
    "aqa",
    "learnlm",
    "nano-banana",
    "veo",
    "imagen",
)
# Préfixes de générations fermées aux nouveaux comptes (404 "no longer available").
DEPRECIES = ("models/gemini-1.", "models/gemini-2.")

# Codes HTTP transitoires : on retente au lieu de disqualifier le provider.
TRANSITOIRES = (429, 500, 502, 503, 504)
MAX_MODELES = 3  # nb de modèles essayés chez un provider avant bascule


def _utilisable(mid):
    """Vrai si le modèle est un candidat crédible pour du chat."""
    bas = mid.lower()
    if any(x in bas for x in EXCLUS):
        return False
    if mid.startswith(DEPRECIES):
        return False
    return True


def candidats(provider):
    """Modèles chat retenus, du plus prometteur au moins, ou [] si indisponible."""
    lm = list_models(provider)
    if not lm.get("available"):
        return []
    retenus = [m for m in lm.get("models", []) if _utilisable(m)]
    # "latest" et "flash" d'abord : stables et rapides, ce que veut une cascade.
    retenus.sort(key=lambda m: (0 if "latest" in m else 1, 0 if "flash" in m else 1))
    return retenus


def list_models(provider):
    """Découverte live du catalogue (jamais hardcodé)."""
    pcfg = PROVIDERS[provider]
    if not _key(pcfg):
        return {"provider": provider, "available": False, "reason": "no_api_key"}
    r = _req(pcfg["base_url"] + "/models", _headers(pcfg))
    if not r["ok"]:
        return {
            "provider": provider,
            "available": False,
            "status": r["status"],
            "reason": r.get("error", ""),
        }
    try:
        parsed = json.loads(r["body"])
        ids = [m.get("id") for m in parsed.get("data", []) if m.get("id")]
    except Exception:  # noqa
        ids = []
    return {
        "provider": provider,
        "available": True,
        "latency_ms": r["latency_ms"],
        "model_count": len(ids),
        "models": ids[:50],
    }


def scan():
    """Ping tous les providers, classe par dispo puis latence*poids."""
    results = []
    for name in PROVIDERS:
        res = list_models(name)
        res["weight"] = PROVIDERS[name]["weight"]
        res["note"] = PROVIDERS[name]["note"]
        results.append(res)

    # tri : dispo d'abord, puis meilleur score (latence / poids)
    def score(x):
        if not x.get("available"):
            return (1, 9e9)
        lat = x.get("latency_ms", 9e9)
        return (0, lat / max(x["weight"], 0.1))

    results.sort(key=score)
    return {
        "scan": results,
        "cascade_order": [r["provider"] for r in results if r.get("available")],
    }


def chat(prompt, provider=None, model=None, cascade=True):
    """
    Envoie prompt. Si provider donné -> direct. Sinon cascade par priorité.
    Bascule au provider suivant si échec.
    """
    order = (
        [provider]
        if provider
        else [p for p in sorted(PROVIDERS, key=lambda k: -PROVIDERS[k]["weight"])]
    )
    attempts = []
    for name in order:
        pcfg = PROVIDERS.get(name)
        if not pcfg:
            attempts.append(
                {"provider": name, "ok": False, "reason": "unknown_provider"}
            )
            continue
        if not _key(pcfg):
            attempts.append({"provider": name, "ok": False, "reason": "no_api_key"})
            if not cascade:
                break
            continue
        # Un modèle imposé court-circuite la sélection ; sinon on prend les
        # meilleurs candidats du catalogue live, filtrés des dépréciés.
        modeles = [model] if model else candidats(name)[:MAX_MODELES]
        if not modeles:
            attempts.append({"provider": name, "ok": False, "reason": "no_model_found"})
            if not cascade:
                break
            continue

        for mdl in modeles:
            payload = {"model": mdl, "messages": [{"role": "user", "content": prompt}]}
            r = _req(
                pcfg["base_url"] + "/chat/completions",
                _headers(pcfg),
                payload=payload,
                method="POST",
            )
            if r["ok"]:
                try:
                    parsed = json.loads(r["body"])
                    text = parsed["choices"][0]["message"]["content"]
                    usage = parsed.get("usage", {})
                except Exception as e:  # noqa
                    attempts.append(
                        {
                            "provider": name,
                            "model": mdl,
                            "ok": False,
                            "reason": "parse_error:" + str(e)[:120],
                        }
                    )
                    continue
                return {
                    "ok": True,
                    "provider": name,
                    "model": mdl,
                    "latency_ms": r["latency_ms"],
                    "usage": usage,
                    "response": text,
                    "attempts": attempts,
                }

            transitoire = r["status"] in TRANSITOIRES
            attempts.append(
                {
                    "provider": name,
                    "model": mdl,
                    "ok": False,
                    "status": r["status"],
                    "transitoire": transitoire,
                    "reason": r.get("error", "")[:200],
                }
            )
            # 503/429 = saturation passagère : une pause courte suffit souvent.
            # 404 = modèle mort : inutile d'attendre, on passe au suivant.
            if transitoire:
                time.sleep(1.0)

        if not cascade:
            break
    return {"ok": False, "reason": "all_providers_failed", "attempts": attempts}


def main():
    ap = argparse.ArgumentParser(description="multi_ai_router jarvis-turbo handler")
    ap.add_argument("--once", action="store_true", help="run once and exit")
    ap.add_argument("--action", choices=["scan", "models", "chat"], default="scan")
    ap.add_argument("--provider", help="groq|cerebras|gemini|mistral|openrouter")
    ap.add_argument("--model", help="force un model id (sinon auto)")
    ap.add_argument("--prompt", help="prompt pour --action chat")
    ap.add_argument("--no-cascade", action="store_true")
    args = ap.parse_args()

    if args.action == "scan":
        out = scan()
    elif args.action == "models":
        if not args.provider:
            out = {"error": "--provider requis pour models"}
        else:
            out = list_models(args.provider)
    elif args.action == "chat":
        if not args.prompt:
            out = {"error": "--prompt requis pour chat"}
        else:
            out = chat(
                args.prompt,
                provider=args.provider,
                model=args.model,
                cascade=not args.no_cascade,
            )
    else:
        out = {"error": "unknown action"}

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
