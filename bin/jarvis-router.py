#!/usr/bin/env python3
"""jarvis-router.py — routeur par SOURCE du planner de production JARVIS.

route(title, cmd) → (source, intent) déterministe, puis handler read-only/safe de la source
avec DISPONIBILITÉ vérifiée + FALLBACK. Aucune action sortante auto (envoi/write = approbation).

  jarvis-router.py --test "<phrase>"     route + exécute le handler safe + montre la sortie
  jarvis-router.py --route "<phrase>"    imprime juste (source, intent) sans exécuter

Couches séparées : routage (route) · exécution (handlers) · notification (telegram dry-run).
Idempotent, logs ~/.local/share/jarvis-router.log, retries 1× sur handler transient.
"""

import json
import os
import re
import subprocess
import time

HOME = os.path.expanduser("~")
ENV = os.path.join(HOME, ".config", "jarvis", ".env")
LOG = os.path.join(HOME, ".local", "share", "jarvis-router.log")
GH_OWNER = "Turbo31150"


def log(m):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    line = "%s %s" % (time.strftime("%F %T"), m)
    try:
        open(LOG, "a", encoding="utf-8").write(line + "\n")
    except Exception:
        pass


def _env_has(key):
    try:
        for ln in open(ENV, encoding="utf-8"):
            if (
                ln.startswith(key + "=")
                and ln.strip() != key + "="
                and len(ln.split("=", 1)[1].strip()) > 3
            ):
                return True
    except Exception:
        pass
    return False


def _run(argv, timeout=15):
    try:
        r = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
        )
        return (r.returncode == 0), ((r.stdout or "") + (r.stderr or "")).strip()
    except Exception as e:
        return False, str(e)


# ── ROUTAGE (couche 1) ──────────────────────────────────────────────────────
_SRC = [
    (
        "github",
        r"(github|pull request|\bprs?\b|issues?|commits?|repos?|dépôts?|ci/cd|\bci\b|releases?|\bmerge\b|branch)",
    ),
    (
        "notion",
        r"\b(notion|documentation|\bdoc\b|backlog|sop|note|base de connaissance|knowledge)\b",
    ),
    (
        "ollama",
        r"\b(ollama|modèle|model|benchmark|inference|quantiz|llm local|ia locale|offline)\b",
    ),
    (
        "youtube",
        r"\b(youtube|vidéo|video|ctr|audience|rétention|miniature|thumbnail|chaîne|abonn)\b",
    ),
    (
        "gtasks",
        r"\b(rappel|rappelle|échéance|deadline|todo daté|reminder|planifie.*(demain|le \d))\b",
    ),
    (
        "telegram",
        r"\b(alerte|alert|notifie|notification|telegram|broadcast|préviens|ping)\b",
    ),
    (
        "mcp",
        r"\b(santé|health|monitoring|service|orchestr|script|cluster|système|status|gpu|infra)\b",
    ),
]
_INTENT = [
    ("veille", r"\b(surveille|veille|monitor|watch|suis)\b"),
    ("rappel", r"\b(rappelle|rappel|reminder|échéance|deadline)\b"),
    ("audit", r"\b(audit|audite|vérifie|scan|analyse)\b"),
    ("reporting", r"\b(résume|résumé|rapport|report|synthèse|bilan)\b"),
    ("exécution", r"\b(lance|exécute|démarre|run|déclenche|fais)\b"),
]


def route(text):
    t = (text or "").lower()
    src = "code"
    for name, rx in _SRC:
        if re.search(rx, t):
            src = name
            break
    intent = "exécution"
    for name, rx in _INTENT:
        if re.search(rx, t):
            intent = name
            break
    return src, intent


# ── HANDLERS par source (couche 2) — read-only/safe, dispo + fallback ───────
def h_github(text):
    if re.search(r"issue", text, re.I):
        ok, out = _run(
            [
                "gh",
                "search",
                "issues",
                "--owner",
                GH_OWNER,
                "--state",
                "open",
                "--limit",
                "8",
            ]
        )
    elif re.search(r"\bpr\b|pull", text, re.I):
        ok, out = _run(
            [
                "gh",
                "search",
                "prs",
                "--owner",
                GH_OWNER,
                "--state",
                "open",
                "--limit",
                "8",
            ]
        )
    else:
        ok, out = _run(["gh", "repo", "list", GH_OWNER, "--limit", "8"])
    return ("done" if ok else "blocked"), out[:2000]


def h_ollama(text):
    ok, out = _run(["curl", "-s", "--max-time", "5", "http://127.0.0.1:11434/api/tags"])
    if ok and out:
        try:
            models = [m["name"] for m in json.loads(out).get("models", [])]
            return "done", "Ollama local — %d modèles: %s" % (
                len(models),
                ", ".join(models[:12]),
            )
        except Exception:
            pass
    ok2, out2 = _run(
        ["curl", "-s", "--max-time", "5", "http://127.0.0.1:1234/v1/models"]
    )  # fallback LMS
    return ("done" if ok2 else "blocked"), "fallback LM Studio :1234\n" + out2[:1000]


def h_mcp(text):
    ok, out = _run(["curl", "-s", "--max-time", "4", "http://127.0.0.1:8000/health"])
    if ok and out:
        return "done", "jarvis-mcp :8000 " + out[:500]
    # fallback : exécution locale directe (services user critiques)
    ok2, out2 = _run(
        [
            "systemctl",
            "--user",
            "is-active",
            "lms-runaway-guard",
            "jarvis-planning-widget",
            "jarvis-producer.timer",
        ]
    )
    return "done", "fallback local (mcp :8000 down) — services:\n" + out2[:500]


def h_telegram(text):
    # notification = SORTANT → dry-run seulement, envoi réel = approbation
    ok, out = _run(
        [
            "bash",
            os.path.join(HOME, "jarvis", "bin", "telegram-state-report.sh"),
            "--dry-run",
        ],
        20,
    )
    return "done", "[DRY-RUN — envoi réel = approbation]\n" + out[:1500]


def _cdp_available():
    """Retourne un endpoint CDP/BrowserOS vivant (0-API), ou 0."""
    for p in (9222, 9108):
        ok, _ = _run(
            [
                "curl",
                "-s",
                "-o",
                "/dev/null",
                "--max-time",
                "2",
                "http://127.0.0.1:%d/json/version" % p,
            ]
        )
        if ok:
            return p
    ok, _ = _run(
        [
            "curl",
            "-s",
            "-o",
            "/dev/null",
            "--max-time",
            "2",
            "http://127.0.0.1:9201/health",
        ]
    )
    return 9201 if ok else 0


def _cdp_route(url, label):
    """Route 0-API via le navigateur (CDP/BrowserOS). N'OUVRE PAS d'onglet
    (le producteur tourne en continu — pas de spam) : confirme la voie navigateur.
    L'extraction réelle = agentique (ia-web-jarvis / session Claude) sur la session connectée."""
    p = _cdp_available()
    if not p:
        return (
            "blocked",
            "0-API navigateur indispo (ni CDP 9222/9108 ni BrowserOS 9201)",
        )
    return "done", (
        "0-API via NAVIGATEUR (CDP :%d) — %s\n  URL: %s\n"
        "  Voie: session Chrome connectée + ia-web-jarvis/BrowserOS (aucune clé API requise).\n"
        "  Extraction agentique à la demande ; le routeur confirme la voie navigateur dispo."
        % (p, label, url)
    )


def h_notion(text):
    if not _env_has("NOTION_API_KEY"):
        return _cdp_route("https://www.notion.so", "Notion (0-API navigateur)")
    ok, out = _run(
        [
            "curl",
            "-s",
            "--max-time",
            "6",
            "-X",
            "POST",
            "http://127.0.0.1:8000/mcp",
            "-H",
            "Content-Type: application/json",
            "-d",
            '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"notion_query_database","arguments":{}}}',
        ]
    )
    return ("done" if ok else "blocked"), out[:1500]


def h_youtube(text):
    if not _env_has("YOUTUBE_API_KEY"):
        return _cdp_route(
            "https://studio.youtube.com", "YouTube Studio (0-API navigateur)"
        )
    ok, out = _run(
        [
            "curl",
            "-s",
            "--max-time",
            "6",
            "-X",
            "POST",
            "http://127.0.0.1:8000/mcp",
            "-H",
            "Content-Type: application/json",
            "-d",
            '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"youtube_channel_stats","arguments":{}}}',
        ]
    )
    return ("done" if ok else "blocked"), out[:1500]


def h_gtasks(text):
    # aucun connecteur natif → fallback jarvis-plan --add (rappel dans le planning)
    titre = (text or "rappel")[:80]
    return (
        "fallback",
        'Google Tasks non câblé → FALLBACK : jarvis-plan.py --add "%s" --priorite P1'
        % titre,
    )


HANDLERS = {
    "github": h_github,
    "ollama": h_ollama,
    "mcp": h_mcp,
    "telegram": h_telegram,
    "notion": h_notion,
    "youtube": h_youtube,
    "gtasks": h_gtasks,
}


def dispatch(text):
    src, intent = route(text)
    handler = HANDLERS.get(src)
    if not handler:
        return (
            src,
            intent,
            "code",
            "→ tâche de code : dispatch omega-dev-agent (session Claude), hors routeur.",
        )
    for attempt in (1, 2):  # retry 1× sur transient
        status, out = handler(text)
        if status != "blocked" or attempt == 2:
            break
        time.sleep(0.5)
    log("route=%s intent=%s status=%s :: %s" % (src, intent, status, text[:80]))
    return src, intent, status, out


def main():
    import argparse

    ap = argparse.ArgumentParser(prog="jarvis-router")
    ap.add_argument("--test", metavar="PHRASE", help="route + exécute le handler safe")
    ap.add_argument(
        "--route", metavar="PHRASE", help="imprime (source,intent) sans exécuter"
    )
    a = ap.parse_args()
    if a.route:
        s, i = route(a.route)
        print("source=%s · intent=%s" % (s, i))
    elif a.test:
        s, i, st, out = dispatch(a.test)
        print("═══ route=%s · intent=%s · statut=%s ═══" % (s, i, st))
        print(out)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
