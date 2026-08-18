#!/usr/bin/env python3
"""jarvis-source-router.py — COUCHE ROUTAGE : route une tâche vers la bonne SOURCE
(GitHub, Notion, JARVIS MCP, Ollama, YouTube, Google Tasks, Telegram) + FLUX
(veille|rappel|audit|execution|reporting), puis exécute l'action RÉELLE par source.

Principes production : DRY par défaut (--go pour tout outward), args validés (no-shell),
idempotence, logs structurés, retries, JAMAIS inventer un connecteur (notion/youtube
sans clé → fallback + flag). Réutilise jarvis-prod-exec (doc/commit/_generate).

Usage :
  jarvis-source-router.py --dry --task "<titre>"     # classifie + montre l'action (0 effet)
  jarvis-source-router.py --go  --task "<titre>"      # exécute réellement (outward inclus)
  jarvis-source-router.py --rules                     # liste les règles
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.expanduser("~/jarvis")
ROUTES = f"{ROOT}/data/source_routes.json"
PROD = f"{ROOT}/bin/jarvis-prod-exec.py"
LOG = f"{ROOT}/logs/source-router.log"
HUB = "http://127.0.0.1:18800/v1/chat/completions"

_NAME_OK = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def log(source, flux, task, action, status):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}][{status}][{source}/{flux}] {action} :: {task[:80]}"
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    return line


# ─────────────────────── COUCHE 1 : classification ───────────────────────
def load_rules():
    try:
        return json.load(open(ROUTES, encoding="utf-8"))
    except Exception:
        return {"rules": [], "default": {"source": "mcp", "flux": "execution"}}


def classify(task: str) -> dict:
    cfg = load_rules()
    low = (task or "").lower()
    for r in cfg.get("rules", []):
        for kw in r.get("keywords", []):
            if kw in low:
                return {"source": r["source"], "flux": r["flux"], "why": kw}
    d = cfg.get("default", {"source": "mcp", "flux": "execution"})
    return {"source": d["source"], "flux": d["flux"], "why": "défaut"}


# ─────────────────────── COUCHE 2 : exécution par source ───────────────────────
def _prod(action, task):
    """Réutilise jarvis-prod-exec (doc/commit) — pas de duplication."""
    try:
        r = subprocess.run(
            [
                "python3",
                PROD,
                action,
                "--task",
                task,
                *(["--go"] if "--go" in sys.argv else []),
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return f"[prod-exec échec: {e}]"


def _gh_issue(task, go):
    title = task[:120]
    if not go:
        return f'DRY: gh issue create --title "{title}" (repo courant)'
    # idempotence : ne recrée pas une issue au titre identique
    try:
        existing = subprocess.run(
            [
                "gh",
                "issue",
                "list",
                "--search",
                title,
                "--json",
                "title",
                "--limit",
                "5",
            ],
            capture_output=True,
            text=True,
            timeout=20,
        ).stdout
        if title.lower() in existing.lower():
            return f"idempotent: issue '{title[:40]}' existe déjà"
        r = subprocess.run(
            [
                "gh",
                "issue",
                "create",
                "--title",
                title,
                "--body",
                f"Auto-créée par jarvis-source-router · {task}",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return (r.stdout + r.stderr).strip() or "issue créée"
    except Exception as e:
        return f"[gh échec: {e}]"


def _telegram(task, go):
    tok = os.getenv("TELEGRAM_TOKEN") or os.getenv("JARVIS_TELEGRAM_TOKEN")
    chat = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("JARVIS_TELEGRAM_CHAT")
    msg = f"🔔 JARVIS · {task[:200]}"
    if not go:
        return f"DRY: telegram sendMessage → « {msg[:60]} »"
    if not tok or not chat:
        return "[telegram: token/chat absent → non envoyé]"
    try:
        import urllib.parse

        data = urllib.parse.urlencode({"chat_id": chat, "text": msg}).encode()
        for _ in range(2):  # retry contrôlé
            try:
                urllib.request.urlopen(
                    f"https://api.telegram.org/bot{tok}/sendMessage",
                    data=data,
                    timeout=8,
                )
                return "alerte Telegram envoyée"
            except Exception:
                time.sleep(1)
        return "[telegram: échec après retry]"
    except Exception as e:
        return f"[telegram échec: {type(e).__name__}]"


def _ollama(task, go):
    """Génération/analyse via hub :18800 (failover). Toujours local, auto."""
    try:
        payload = json.dumps(
            {
                "messages": [
                    {"role": "user", "content": f"Analyse concise (IA locale): {task}"}
                ],
                "max_tokens": 400,
            }
        ).encode()
        req = urllib.request.Request(
            HUB, data=payload, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read().decode())
        txt = (
            d.get("choices", [{}])[0].get("message", {}).get("content") or ""
        ).strip()
        return f"ollama/hub → {txt[:200]}" if txt else "[ollama: vide]"
    except Exception as e:
        return f"[ollama échec: {e}]"


def execute(route: dict, task: str, go: bool) -> str:
    src, flux = route["source"], route["flux"]
    # DRY strict : décrit l'action prévue SANS aucun appel réel (0 effet, 0 fichier)
    if "--dry" in sys.argv:
        plan = {
            "github": "gh issue create / prod-exec commit",
            "mcp": "prod-exec doc (document réel) ou route script/domino",
            "ollama": "génération/analyse via hub :18800",
            "telegram": "telegram sendMessage (outward)",
            "gtasks": "FALLBACK → Google Calendar via MCP",
            "notion": "FALLBACK → doc local + flag (clé absente)",
            "youtube": "FLAG connecteur à configurer (aucune action)",
        }.get(src, "action inconnue")
        return f"DRY (0 effet) · action prévue: {plan}"
    if src == "github":
        # code/commit → prod-exec commit ; sinon issue
        if re.search(r"committer|reviewer|commit\b|fichier", task, re.I):
            return _prod("commit", task)
        return _gh_issue(task, go)
    if src == "mcp":
        # exécution locale : rédiger/créer → doc réel ; sinon note
        if re.search(
            r"rédiger|rediger|créer|creer|politique|checklist|registre|guide|document|procédure",
            task,
            re.I,
        ):
            return _prod("doc", task)
        return f"MCP local: tâche '{task[:50]}' → à router vers script/domino"
    if src == "ollama":
        return _ollama(task, go)
    if src == "telegram":
        return _telegram(task, go)
    if src == "gtasks":
        # pas de connecteur GTasks direct → fallback Calendar (via orchestrateur/MCP) : FLAG
        return f"FALLBACK: rappel « {task[:50]} » → Google Calendar via MCP (orchestrateur) [flux={flux}]"
    if src == "notion":
        # clé absente → fallback doc local + flag
        r = _prod("doc", task)
        return f"FALLBACK Notion (clé absente): doc local produit + à pousser Notion · {r.splitlines()[-1] if r else ''}"
    if src == "youtube":
        return "FLAG: connecteur YouTube Analytics à configurer (YOUTUBE_API_KEY vide) — aucune action inventée"
    return f"[source inconnue: {src}]"


def main() -> int:
    if "--rules" in sys.argv:
        print(json.dumps(load_rules(), ensure_ascii=False, indent=2))
        return 0
    task = sys.argv[sys.argv.index("--task") + 1] if "--task" in sys.argv else ""
    if not task:
        print(__doc__)
        return 2
    go = "--go" in sys.argv
    route = classify(task)
    print(f"→ SOURCE={route['source']} FLUX={route['flux']} (règle: {route['why']})")
    out = execute(route, task, go)
    status = "GO" if go else "DRY"
    print(f"  [{status}] {out}")
    log(route["source"], route["flux"], task, out[:60], status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
