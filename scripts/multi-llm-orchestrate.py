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
    ("M6", "http://10.42.0.230:1234/v1/chat/completions", "qwen3.5-9b", 1.5),  # 2026-08-19: 127.0.0.1:1234 mort (pas de LM Studio sur M4), bascule sur le cable direct M6
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
    # Poids TOTAL demandé, muets compris. Sans ça, un backend absent disparaît du
    # dénominateur : le 19/08/2026 M6 (poids 1.5 sur 4.1, soit 37 %) rendait 400 et
    # le verdict sortait quand même « FORT 1.0 ». Un consensus qui ne compte que
    # ceux qui ont répondu ne mesure pas l'accord, il mesure la présence.
    poids_demande = sum(r.get("weight", 0) for r in responses) or 1.0
    muets = [r["node"] for r in responses if not r.get("text")]
    poids_muet = sum(r.get("weight", 0) for r in responses if not r.get("text"))
    quorum = round(1 - poids_muet / poids_demande, 3)
    if not resp:
        return {"winner": None, "agreement": "FAIBLE", "score": 0.0, "groups": [],
                "quorum": 0.0, "muets": muets}
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
    # Un accord entre survivants n'est pas un accord du cluster : sous 2/3 du poids
    # demandé, on refuse le label FORT quelle que soit la similarité.
    if quorum < 0.67:
        agreement = "PARTIEL"
    return {
        "winner": winner,
        "agreement": agreement,
        "score": score,
        "quorum": quorum,
        "muets": muets,
        "groups": [[x["node"] for x in g] for g in groups],
    }


def _ask(node, url, model, prompt, timeout=60):
    """Interroge un backend. Utilise /v1/completions avec <think></think> pre-ferme
    sur les serveurs LM Studio.

    CORRIGE LE 19/08/2026. Les modeles qwen3 / qwen3.5 rangent tout leur raisonnement
    dans reasoning_content et laissent content VIDE sur /v1/chat/completions. Mesure :
    qwen3-4b rend 0 caractere de contenu contre 677 de raisonnement. Consequence ici :
    le backend M6, qui porte le POIDS LE PLUS LOURD du vote (1.5), rendait une chaine
    vide a chaque appel. Le consensus se calculait donc sur les autres backends en
    croyant l avoir consulte — d ou des verdicts FAIBLE inexpliques. Aucune erreur
    n etait levee : text="" est indistinguable d une reponse legitimement courte.

    Fermer <think> d avance supprime la phase de raisonnement : le modele repond."""
    lmstudio = url.endswith("/v1/chat/completions") and ":1234" in url
    if lmstudio:
        url = url.replace("/v1/chat/completions", "/v1/completions")
        body = json.dumps({
            "model": model,
            "prompt": f"<|im_start|>user\n{prompt}<|im_end|>\n"
                      f"<|im_start|>assistant\n<think></think>\n\n",
            "temperature": 0.2, "max_tokens": 512, "stop": ["<|im_end|>"],
        }).encode()
    else:
        body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2, "max_tokens": 512,
        }).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
        choix = (data.get("choices") or [{}])[0]
        if lmstudio:
            texte = (choix.get("text") or "").strip()
        else:
            m = choix.get("message", {}) or {}
            texte = (m.get("content") or "").strip()
            if not texte:
                # meme defaut possible derriere un proxy : on etiquette plutot que
                # de rendre du vide silencieux
                r_ = (m.get("reasoning_content") or "").strip()
                texte = f"[{node} — raisonnement brut]\n{r_[-800:]}" if r_ else ""
        if not texte:
            return {"node": node, "text": "", "error": "contenu vide"}
        return {"node": node, "text": texte}
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
        muets = f" · muets: {','.join(v['muets'])}" if v.get("muets") else ""
        print(f"[{v['winner']['node']}] ({v['agreement']} accord={v['score']} "
              f"quorum={v.get('quorum')}{muets})")
        print(v["winner"]["text"])
    else:
        print("Aucune réponse des backends.", file=sys.stderr)
        sys.exit(1)
