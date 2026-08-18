#!/usr/bin/env python3
"""Orchestrateur multi-LLM : fan-out M1/M2/OL1 + vote pondéré par similarité.
0 token API Anthropic — tout local. Réutilisable par skills/agents JARVIS."""

import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher

# (node, url chat-completions OpenAI-compat, model, weight)
# Poids = barème canonique N1 du skill weighted-orchestration (M3 1.8 down, M1 1.5, OL1 1.4, M2 1.2)
BACKENDS = [
    ("M1", "http://127.0.0.1:1234/v1/chat/completions", "qwen3.5-9b", 1.5),
    ("M2", "http://127.0.0.1:18800/v1/chat/completions", "qwen3.5-9b", 1.2),
    ("OL1", "http://127.0.0.1:11434/v1/chat/completions", "gemma3:4b", 1.4),
]


def _sim(a, b):
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def weighted_vote(responses, threshold=0.6):
    """responses: [{node, weight, text}]. Retourne le gagnant (réponse au plus fort
    poids cumulé de son groupe de similarité) + verdict FORT/FAIBLE.
    Fonction PURE — aucune I/O, testable offline."""
    resp = [r for r in responses if r.get("text")]
    if not resp:
        return {"winner": None, "agreement": "FAIBLE", "score": 0.0, "groups": []}
    # Regroupe par similarité >= threshold
    groups = []
    for r in resp:
        placed = False
        for g in groups:
            if _sim(r["text"], g[0]["text"]) >= threshold:
                g.append(r)
                placed = True
                break
        if not placed:
            groups.append([r])
    # Poids cumulé par groupe
    best = max(groups, key=lambda g: sum(x["weight"] for x in g))
    best_weight = sum(x["weight"] for x in best)
    total_weight = sum(x["weight"] for x in resp)
    winner = max(best, key=lambda x: x["weight"])
    score = round(best_weight / total_weight, 3)
    agreement = (
        "FORT"
        if (len(best) >= 2 and score >= threshold) or len(resp) == 1
        else "FAIBLE"
    )
    return {
        "winner": winner,
        "agreement": agreement,
        "score": score,
        "groups": [[x["node"] for x in g] for g in groups],
    }


def _ask(node, url, model, prompt, timeout=60):
    body = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 512,
        }
    ).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
        return {"node": node, "text": data["choices"][0]["message"]["content"]}
    except Exception as e:
        return {"node": node, "text": "", "error": str(e)}


def orchestrate(prompt, threshold=0.6):
    """Fan-out parallèle vers tous les backends, puis vote pondéré."""
    weights = {n: w for n, _, _, w in BACKENDS}
    results = []
    with ThreadPoolExecutor(max_workers=len(BACKENDS)) as ex:
        futs = {ex.submit(_ask, n, u, m, prompt): n for n, u, m, w in BACKENDS}
        for f in as_completed(futs):
            res = f.result()
            res["weight"] = weights[res["node"]]
            results.append(res)
    verdict = weighted_vote(results, threshold=threshold)
    return {"prompt": prompt, "responses": results, "verdict": verdict}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('usage: multi-llm-orchestrate.py "<prompt>" [threshold]', file=sys.stderr)
        sys.exit(2)
    th = float(sys.argv[2]) if len(sys.argv) > 2 else 0.6
    out = orchestrate(sys.argv[1], threshold=th)
    v = out["verdict"]
    if v["winner"]:
        print(f"[{v['winner']['node']}] ({v['agreement']} {v['score']})")
        print(v["winner"]["text"])
    else:
        print("Aucune réponse des backends.", file=sys.stderr)
        sys.exit(1)
