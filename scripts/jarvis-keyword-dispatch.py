#!/usr/bin/env python3
"""jarvis-keyword-dispatch.py — délégation auto par détection de mots-clés.

Détecte l'intention d'une requête via data/dispatch_rules.json (1er match gagne)
et délègue vers la cible : lane du hub LLM (:18800), CLI gratuit (gemini/agy),
outil (research-library) ou chaîne domino (jarvis_master).

Usage :
  jarvis-keyword-dispatch.py "ma requête ..."        # route + exécute
  jarvis-keyword-dispatch.py --dry "ma requête"      # montre la cible sans exécuter
  jarvis-keyword-dispatch.py --rules                 # liste les règles
stdlib uniquement.
"""

import os
import re
import sys
import json
import subprocess
import urllib.request

ROOT = "/home/pamerys/jarvis"
RULES_FILE = os.environ.get("DISPATCH_RULES", f"{ROOT}/data/dispatch_rules.json")
HUB = os.environ.get("JARVIS_HUB", "http://127.0.0.1:18800")
LMS = os.environ.get("JARVIS_LMS", "http://127.0.0.1:1234")
OPENCLAW = os.environ.get("OPENCLAW_BIN", "openclaw")

DEFAULTS = {
    "rules": [
        {
            "keywords": [
                "cahier des charges",
                "protocole",
                "deep research",
                "bibliothèque",
                "audit",
                "code",
                "raisonnement",
                "rapide",
            ],
            "action": "lane:jarvis-auto",
        }
    ],
    "default": "lane:jarvis-auto",
}


def load_rules():
    try:
        return json.load(open(RULES_FILE, encoding="utf-8"))
    except Exception:
        return DEFAULTS


def detect(prompt, cfg):
    p = prompt.lower()
    for r in cfg.get("rules", []):
        for kw in r.get("keywords", []):
            if kw.lower() in p:
                return r["action"], r.get("why", ""), kw
    return cfg.get("default", "lane:jarvis-auto"), "défaut", None


def run_hub_lane(lane, prompt):
    body = json.dumps(
        {
            "model": lane,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 800,
        }
    ).encode()
    req = urllib.request.Request(
        f"{HUB}/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read())
    return d["choices"][0]["message"]["content"], d.get("model", lane)


def run_lms(model, prompt):
    """Inférence directe LM Studio (:1234). model ex: google/gemma-4-e4b.
    Fallback content->reasoning_content (modèles reasoning type qwen3.5)."""
    body = json.dumps(
        {
            "model": model or "google/gemma-4-e4b",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2048,
        }
    ).encode()
    req = urllib.request.Request(
        f"{LMS}/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read())
    m = d["choices"][0]["message"]
    txt = m.get("content") or m.get("reasoning_content") or ""
    return txt, f"lms:{d.get('model', model)}"


def run_agent(name, prompt):
    """Délègue à une flotte d'agents OpenClaw (omega/cowork/openclaw) via la
    Gateway : openclaw agent --agent <id> --message <prompt>. Fallback hub."""
    cmd = [
        OPENCLAW,
        "agent",
        "--agent",
        name or "main",
        "--message",
        prompt,
        "--timeout",
        "120",
    ]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
        out = (p.stdout or "").strip()
        if p.returncode == 0 and out and "Unknown agent" not in out:
            return out, f"agent:{name}"
    except Exception:  # noqa: BLE001
        pass
    txt, model = run_hub_lane("jarvis-auto", prompt)
    return txt, f"agent:{name}→hub:{model}"


def run_cli(tool, prompt):
    if tool == "gemini":
        cmd = [os.path.expanduser("~/.local/bin/gemini"), "-p", prompt]
    elif tool == "agy":
        cmd = [
            os.path.expanduser("~/.local/bin/agy"),
            "-p",
            prompt,
            "--print-timeout",
            "280s",
        ]
    else:
        return f"[dispatch] CLI inconnu: {tool}", tool
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    out = (p.stdout or p.stderr).strip()
    # fallback hub si le CLI échoue/vide
    if p.returncode != 0 or not out or "CLI error" in out:
        txt, model = run_hub_lane("jarvis-auto", prompt)
        return txt, f"{tool}→hub:{model}"
    return out, f"cli:{tool}"


def run_tool(name, prompt):
    if name == "research-library":
        p = subprocess.run(
            ["python3", f"{ROOT}/scripts/research-library.py", "list"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return p.stdout.strip(), "tool:research-library"
    return f"[dispatch] outil inconnu: {name}", name


def run_domino(name, prompt):
    # Montre le plan domino (le pipeline réel est lancé par le skill correspondant)
    p = subprocess.run(
        ["python3", f"{ROOT}/cli/jarvis_master.py", "plan", prompt or name],
        capture_output=True,
        text=True,
        timeout=30,
    )
    plan = p.stdout.strip() or "(plan vide)"
    return (
        f"Chaîne domino '{name}' planifiée pour cette requête.\n{plan}\n"
        f"→ Lance le pipeline via le skill: /jarvis-os:deep-research (ou /audit-mode)."
    ), f"domino:{name}"


# Verbes/mots génériques qui font échouer le AND strict de bloc.sh.
_STOP = {
    "diagnostiquer",
    "reparer",
    "réparer",
    "corriger",
    "verifier",
    "vérifier",
    "lancer",
    "relancer",
    "faire",
    "creer",
    "créer",
    "mettre",
    "gerer",
    "gérer",
    "analyser",
    "checker",
    "regarder",
    "traiter",
    "incident",
    "persistant",
    "le",
    "la",
    "les",
    "un",
    "une",
    "des",
    "du",
    "de",
    "sur",
    "dans",
    "pour",
    "avec",
    "que",
    "qui",
    "est",
    "ce",
    "et",
    "ou",
}


def _bloc_run(query):
    try:
        p = subprocess.run(
            ["bash", f"{ROOT}/bin/bloc.sh", query],
            capture_output=True,
            text=True,
            timeout=20,
        )
    except Exception:
        return None
    out = p.stdout.strip()
    if not out or out.startswith("∅") or "aucun bloc" in out:
        return None
    # lignes de données = celles portant le séparateur bloc "→"
    lines = [l for l in out.splitlines() if "→" in l]
    pref = [
        l
        for l in lines
        if any(t in l for t in ("[serie]", "[cmd", "[domino", "[mode", "[n8n]"))
    ]
    keep = (pref + [l for l in lines if l not in pref])[:8]
    if not keep:
        return None
    return out.splitlines()[0] + "\n" + "\n".join(keep)


def run_biblio(prompt):
    """Route sur la BIBLIOTHÈQUE (bloc.sh) : intention → bloc/commande/série/domino
    prêt. Principe anti-loop : un bloc existe → on l'applique, on ne recalcule pas.

    bloc.sh fait un AND strict de TOUS les mots ; les verbes génériques
    ('diagnostiquer', 'réparer'…) tuent le match. On essaie l'intention entière,
    puis on retombe sur les mots-ENTITÉS significatifs (browseros, gpu, n8n…)."""
    res = _bloc_run(prompt)
    if res:
        return res, "biblio:bloc.sh"
    # fallback : mots significatifs (len>3, hors stopwords), du + long au + court
    words = [
        w
        for w in re.findall(r"[a-zA-Zéèêàçùïî0-9-]{4,}", prompt.lower())
        if w not in _STOP
    ]
    for w in sorted(set(words), key=len, reverse=True):
        res = _bloc_run(w)
        if res:
            return res, f"biblio:bloc.sh({w})"
    return None


def dispatch(prompt, dry=False, route=None):
    cfg = load_rules()
    if route:
        # Route explicite (ex: context.route d'une tâche OMEGA-cascade) : on
        # court-circuite la détection mots-clés ET le fallback biblio — l'item
        # atteint directement son backend (lane/lms/agent/cli/tool/domino).
        action, why, kw = route, "route explicite", "route"
    else:
        action, why, kw = detect(prompt, cfg)
    kind, _, target = action.partition(":")
    # Aucun mot-clé matché → AVANT le LLM générique (qui hallucine), consulter la
    # bibliothèque : tout route sur bibliothèque/action/commande/domino d'abord.
    if kw is None:
        biblio = run_biblio(prompt)
        if biblio:
            txt, model = biblio
            print("[dispatch] défaut → BIBLIOTHÈQUE (bloc.sh)")
            if not dry:
                print(f"--- via {model} ---\n{txt}")
            return 0
    hit = "route explicite" if route else (f"mot-clé '{kw}'" if kw else "défaut")
    print(f"[dispatch] {hit} → {action}  ({why})")
    if dry:
        return 0
    try:
        if kind == "lane":
            txt, model = run_hub_lane(target, prompt)
        elif kind == "cli":
            txt, model = run_cli(target, prompt)
        elif kind == "tool":
            txt, model = run_tool(target, prompt)
        elif kind == "domino":
            txt, model = run_domino(target, prompt)
        elif kind == "lms":
            txt, model = run_lms(target, prompt)
        elif kind == "agent":
            txt, model = run_agent(target, prompt)
        else:
            txt, model = run_hub_lane("jarvis-auto", prompt)
    except Exception as e:  # noqa: BLE001
        print(f"[dispatch] {action} échec ({e}) → fallback hub jarvis-auto")
        txt, model = run_hub_lane("jarvis-auto", prompt)
    print(f"--- via {model} ---\n{txt}")
    return 0


def main(argv):
    if not argv or argv[0] == "--rules":
        cfg = load_rules()
        print(f"=== Règles de délégation ({RULES_FILE}) ===")
        for r in cfg.get("rules", []):
            print(f"  {r['action']:24} ← {', '.join(r['keywords'][:4])}…")
        print(f"  {cfg.get('default'):24} ← (défaut)")
        return 0
    dry = "--dry" in argv
    route = None
    if "--route" in argv:
        i = argv.index("--route")
        route = argv[i + 1] if i + 1 < len(argv) else None
        argv = argv[:i] + argv[i + 2 :]
    prompt = " ".join(a for a in argv if a != "--dry").strip()
    if not prompt:
        print(
            'usage: jarvis-keyword-dispatch.py [--dry|--rules] [--route ACTION] "requête"'
        )
        return 1
    return dispatch(prompt, dry, route)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
