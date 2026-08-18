#!/usr/bin/env python3
"""
jarvis audit — audit STATIQUE de sécurité et d'architecture.

Trois contrôles, tous sans réseau ni LLM :
  (a) loi A1 — aucune brique hors `agent` ne contacte un fournisseur de modèle
  (b) les 9 cibles SSRF obfusquées sont bloquées par le garde de `web`
  (c) les fichiers de secrets sont en 0600

Exit 1 si un contrôle échoue. C'est le garde anti-régression à brancher en CI.
"""

import os
import re
import sys
import json
from pathlib import Path

ROOT = Path(os.environ.get("JARVIS_ROOT", Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(ROOT / "scripts" / "lib"))
import webguard  # noqa: E402

BRIQUES = [
    "mail",
    "media",
    "board",
    "web",
    "publish",
    "mem",
]  # agent EXCLU : c'est la gateway

# Signatures d'un appel direct à un fournisseur de modèle.
SIGNATURES_LLM = re.compile(
    r"(:11434|:1234|/v1/chat/completions|/v1/completions|api\.openai\.com"
    r"|generativelanguage\.googleapis|api\.anthropic\.com|ollama\s+run)",
    re.IGNORECASE,
)

CIBLES_SSRF = [
    "http://127.0.0.1/",
    "http://localhost/",
    "http://169.254.169.254/latest/meta-data/",
    "http://10.0.0.5/",
    "http://[::1]/",
    "http://127.1/",
    "http://2130706433/",
    "http://[::ffff:127.0.0.1]/",
    "file:///etc/passwd",
]

FICHIERS_SECRETS = [
    ROOT / ".env",
    ROOT / "config" / ".env",
    Path.home() / ".jarvis.env",
]


def strip_comments(source):
    """Retire commentaires et docstrings : une mention en prose n'est pas un appel."""
    sans_docstrings = re.sub(r'("""|\'\'\')(?:.|\n)*?\1', "", source)
    return re.sub(r"#.*$", "", sans_docstrings, flags=re.MULTILINE)


def main():
    json_out = "--json" in sys.argv
    resultats = []
    echec = False

    # (a) loi A1
    for b in BRIQUES:
        p = ROOT / "bin" / f"jarvis-{b}"
        if not p.exists():
            continue
        code = strip_comments(p.read_text(encoding="utf-8", errors="replace"))
        hits = SIGNATURES_LLM.findall(code)
        ok = not hits
        echec = echec or not ok
        resultats.append(
            {
                "controle": f"A1 — {b} ne contacte aucun LLM en direct",
                "ok": ok,
                "detail": f"{len(hits)} signature(s)" if hits else "aucune",
            }
        )

    # (b) 9 cibles SSRF
    passees = []
    for url in CIBLES_SSRF:
        try:
            webguard.validate(url)
            passees.append(url)
        except webguard.SSRFBlocked:
            pass
    ok = not passees
    echec = echec or not ok
    resultats.append(
        {
            "controle": "A3 — les 9 cibles SSRF obfusquées sont bloquées",
            "ok": ok,
            "detail": "9/9 bloquées" if ok else f"PASSENT: {passees}",
        }
    )

    # (c) permissions des secrets
    for f in FICHIERS_SECRETS:
        if not f.is_file():
            continue
        mode = oct(f.stat().st_mode & 0o777)
        ok = mode == "0o600"
        echec = echec or not ok
        resultats.append(
            {"controle": f"secrets — {f} en 0600", "ok": ok, "detail": mode}
        )

    if json_out:
        print(
            json.dumps(
                {"ok": not echec, "controles": resultats}, indent=2, ensure_ascii=False
            )
        )
    else:
        print("JARVIS audit — statique, sans réseau ni LLM\n")
        for r in resultats:
            print(
                f"  {'ok   ' if r['ok'] else 'ÉCHEC'} {r['controle']:56} {r['detail']}"
            )
        print()
        print("  ⛔ audit en échec." if echec else "  ✅ audit vert.")
    return 1 if echec else 0


if __name__ == "__main__":
    sys.exit(main())
