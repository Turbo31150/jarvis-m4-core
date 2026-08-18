#!/usr/bin/env python3
"""Shim stdio entre le client MCP et `openclaw acp`.

OpenClaw 2026.7.1-2 renvoie un `initialize` non conforme au schema MCP :
  - protocolVersion en nombre (ex: 1) au lieu d'une chaine ("2024-11-05")
  - capabilities et serverInfo absents
Le client rejette alors la connexion (INVALID_RESULT). Ce shim relaie tout
le trafic tel quel et ne corrige que ces trois champs, sur la seule reponse
a la requete initialize.
"""
from __future__ import annotations

import json
import subprocess
import sys
import threading

PROTOCOL_FALLBACK = "2024-11-05"


def _fix_initialize(payload: dict) -> dict:
    res = payload.get("result")
    if not isinstance(res, dict):
        return payload
    pv = res.get("protocolVersion")
    if isinstance(pv, str) and res.get("serverInfo") and res.get("capabilities") is not None:
        return payload  # deja conforme, on ne touche a rien
    if not isinstance(pv, str):
        res["protocolVersion"] = PROTOCOL_FALLBACK
    res.setdefault("capabilities", {})
    res.setdefault("serverInfo", {"name": "openclaw-acp", "version": "shim"})
    return payload


def main() -> int:
    proc = subprocess.Popen(
        ["openclaw", "acp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        text=True,
        bufsize=1,
    )

    init_ids: set = set()

    def pump_in() -> None:
        try:
            for line in sys.stdin:
                try:
                    msg = json.loads(line)
                    if msg.get("method") == "initialize" and "id" in msg:
                        init_ids.add(msg["id"])
                except (ValueError, AttributeError):
                    pass
                proc.stdin.write(line)
                proc.stdin.flush()
        except (BrokenPipeError, ValueError):
            pass
        finally:
            try:
                proc.stdin.close()
            except OSError:
                pass

    threading.Thread(target=pump_in, daemon=True).start()

    for line in proc.stdout:
        out = line
        stripped = line.strip()
        if stripped.startswith("{"):
            try:
                msg = json.loads(stripped)
                if msg.get("id") in init_ids and "result" in msg:
                    out = json.dumps(_fix_initialize(msg)) + "\n"
                    init_ids.discard(msg["id"])
            except ValueError:
                pass
        sys.stdout.write(out)
        sys.stdout.flush()

    return proc.wait()


if __name__ == "__main__":
    sys.exit(main())
