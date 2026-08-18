#!/usr/bin/env python3
"""
Contrat inter-process lib/proc.py (GAP #3).
Contrôle l'adjacence M2 et le comportement des tuyaux.
"""

import subprocess
import sys
import os
import json

ADJ = {
    "Ω": [
        "agent",
        "mem",
        "web",
        "publish",
        "mail",
        "media",
        "board",
        "deepsearch",
        "Ω",
    ],
    # 8e brique (SOURCER+AGRÉGER, lecture seule) : elle délègue l'analyse à
    # `agent` (A1), persiste via `mem` (A2) et passe toute URL par `web` (A3).
    # Volontairement PAS d'arête vers `publish` : tout effet de bord dérivé
    # est déclenché par Ω après gate humain (A4/A5), jamais par deepsearch.
    "deepsearch": ["agent", "mem", "web"],
    "agent": [],
    "mem": [],
    "web": [],
    "publish": ["agent", "mail"],
    "mail": [],
    "media": ["agent", "web"],
    "board": ["agent", "mem", "web", "media"],
}


def run_brick(
    caller: str,
    callee: str,
    argv: list,
    timeout: int = 120,
    expect_json: bool = True,
    critical: bool = False,
):
    if callee not in ADJ.get(caller, []):
        raise ValueError(
            f"Violation M2: {caller} n'est pas autorisé à appeler {callee}"
        )

    env = os.environ.copy()
    if "JARVIS_COMMAND_ID" not in env:
        env["JARVIS_COMMAND_ID"] = f"cmd_{int(os.getpid())}"

    cmd = [f"/home/pamerys/jarvis/bin/jarvis-{callee}"] + argv
    try:
        res = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, env=env
        )
        if res.returncode != 0 and critical:
            sys.stderr.write(
                f"[proc.py] Échec critique child {callee}: exit {res.returncode}\n"
            )
            sys.exit(res.returncode)

        if expect_json:
            try:
                data = json.loads(res.stdout)
                return res.returncode, data
            except json.JSONDecodeError:
                return res.returncode, {
                    "ok": False,
                    "error": {"code": "E_MALFORMED", "message": res.stdout[:4096]},
                }
        return res.returncode, res.stdout
    except subprocess.TimeoutExpired:
        if critical:
            sys.exit(124)
        return 124, {
            "ok": False,
            "error": {"code": "E_TIMEOUT", "message": f"Timeout {timeout}s dépassé"},
        }
