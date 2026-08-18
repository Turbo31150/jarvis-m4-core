#!/usr/bin/env python3
"""
jarvis doctor — vérifications ACTIVES, avec timeouts courts.

Deux règles qui font la valeur de cette commande :

  - **Aucun appel LLM.** On ping des endpoints, on ne génère jamais. Coût nul,
    quota intact : `doctor` doit pouvoir tourner en boucle sans rien consommer.
  - **Le modèle local est le SEUL check critical.** C'est le plancher souverain :
    si le fallback local ne répond pas, l'écosystème n'a plus de garantie de
    fonctionnement hors fournisseur. Tout le reste est informatif.

Exit 1 si un check critical échoue.
"""

import os
import sys
import json
import time
import socket
import urllib.request
import urllib.error
from pathlib import Path

TIMEOUT = 2.0
ROOT = Path(os.environ.get("JARVIS_ROOT", Path(__file__).resolve().parents[2]))

CHECKS = [
    # (nom, type, cible, critical)
    (
        "LM Studio local (plancher souverain)",
        "http",
        os.environ.get("JARVIS_LMS", "http://127.0.0.1:1234") + "/v1/models",
        True,
    ),
    (
        "hub LLM :18800",
        "http",
        os.environ.get("JARVIS_HUB", "http://127.0.0.1:18800") + "/v1/models",
        False,
    ),
    (
        "Ollama :11434",
        "http",
        os.environ.get("JARVIS_OLLAMA", "http://127.0.0.1:11434") + "/api/tags",
        False,
    ),
    ("widget planning :8899", "tcp", ("127.0.0.1", 8899), False),
]


def check_http(url):
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "jarvis-doctor"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return (
                resp.status < 500,
                f"HTTP {resp.status}",
                int((time.time() - t0) * 1000),
            )
    except urllib.error.HTTPError as exc:
        return exc.code < 500, f"HTTP {exc.code}", int((time.time() - t0) * 1000)
    except Exception as exc:
        return False, f"{type(exc).__name__}", int((time.time() - t0) * 1000)


def check_tcp(hostport):
    t0 = time.time()
    try:
        with socket.create_connection(hostport, timeout=TIMEOUT):
            return True, "port ouvert", int((time.time() - t0) * 1000)
    except Exception as exc:
        return False, f"{type(exc).__name__}", int((time.time() - t0) * 1000)


def main():
    json_out = "--json" in sys.argv
    resultats = []
    echec_critique = False

    for nom, kind, cible, critical in CHECKS:
        ok, detail, ms = check_http(cible) if kind == "http" else check_tcp(cible)
        if critical and not ok:
            echec_critique = True
        resultats.append(
            {"check": nom, "ok": ok, "detail": detail, "ms": ms, "critical": critical}
        )

    # Sanité locale : la policy publish doit exister, sinon publish refuse tout.
    policy = ROOT / "config" / "publish-policy.json"
    resultats.append(
        {
            "check": "policy publish présente",
            "ok": policy.exists(),
            "detail": str(policy),
            "ms": 0,
            "critical": False,
        }
    )

    if json_out:
        print(
            json.dumps(
                {"ok": not echec_critique, "checks": resultats},
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        print(f"JARVIS doctor — checks actifs, timeout {TIMEOUT}s, aucun appel LLM\n")
        for r in resultats:
            marque = "ok  " if r["ok"] else "ÉCHEC"
            crit = " [CRITICAL]" if r["critical"] else ""
            print(f"  {marque} {r['check']:42} {r['detail']:16} {r['ms']:>5} ms{crit}")
        print()
        if echec_critique:
            print(
                "  ⛔ un check CRITICAL échoue — le plancher souverain n'est pas disponible."
            )
        else:
            print("  ✅ tous les checks critiques passent.")
    return 1 if echec_critique else 0


if __name__ == "__main__":
    sys.exit(main())
