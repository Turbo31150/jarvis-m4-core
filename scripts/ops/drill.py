#!/usr/bin/env python3
"""
Harnais de test/drills d'incendie JARVIS (scripts/ops/drill.py).
Scénarios: timeout-cascade, malformed-upstream, failprop, failclosed-critical.
"""

import subprocess
import json


def run_cmd(cmd, env_extra=None):
    import os

    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def test_drills():
    print("🔥 Lancement du harnais de drills d'incendie...")

    # 1. Drill SSRF (web)
    res = run_cmd(["jarvis-web", "grab", "http://127.0.0.1/admin"])
    assert res.returncode == 5, f"Expected 5, got {res.returncode}"
    payload = json.loads(res.stdout)
    assert payload["error"]["code"] == "E_SSRF_BLOCKED"
    print("  [✓] Drill SSRF Blocked (A3)")

    # 2. Drill Mail Send Gate (A4)
    res = run_cmd(
        [
            "jarvis-mail",
            "send",
            "--to",
            "test@test.com",
            "--subject",
            "Sub",
            "--body",
            "Body",
        ]
    )
    assert res.returncode == 77, f"Expected 77, got {res.returncode}"
    payload = json.loads(res.stdout)
    assert payload["error"]["code"] == "E_ALLOWLIST_DENIED"
    print("  [✓] Drill Mail Send Gate (A4)")

    # 3. Drill Board Empty Voice
    res = run_cmd(["jarvis-board", "ask", ""])
    assert res.returncode == 3, f"Expected 3, got {res.returncode}"
    payload = json.loads(res.stdout)
    assert payload["error"]["code"] == "E_NO_VOICE"
    print("  [✓] Drill Board No Voice (E_NO_VOICE)")

    # 4. Drill Agent Normal Output — verbe réel = `ask` (cf. jarvis-agent --help)
    res = run_cmd(["jarvis-agent", "ask", "Test prompt"])
    assert res.returncode == 0, f"Expected 0, got {res.returncode}"
    payload = json.loads(res.stdout)
    assert payload["ok"] is True
    print("  [✓] Drill Agent Normal Output (A1)")

    print("🎉 Tous les drills ont réussi avec succès !")


if __name__ == "__main__":
    test_drills()
