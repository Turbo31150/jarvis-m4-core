#!/usr/bin/env python3
"""auto-debug.py — Scan + fix automatique basé sur KB JSON.

Usage:
  python3 auto-debug.py scan          # détecte les issues
  python3 auto-debug.py scan --json   # sortie JSON
  python3 auto-debug.py fix           # scan + applique les fixes
  python3 auto-debug.py fix --dry-run # scan + affiche les fixes sans les appliquer
"""

from __future__ import annotations
import json
import os
import re
import socket
import subprocess
import sys
from pathlib import Path

KB_PATH = (
    Path(os.environ.get("JARVIS_DATA", Path.home() / "jarvis/data"))
    / "autodebug-kb.json"
)


def _check_port(host: str, port: int) -> bool:
    """Retourne True si le port répond (service UP)."""
    try:
        with socket.create_connection((host, port), timeout=3):
            return True
    except OSError:
        return False


def _check_http(url: str) -> bool:
    import urllib.request

    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.status < 400
    except Exception:
        return False


def _check_grep(file_path: str, pattern: str) -> bool:
    """Retourne True si le pattern est trouvé (check = service OK)."""
    fp = Path(file_path.replace("~", str(Path.home())))
    if not fp.exists():
        return False
    return bool(re.search(pattern, fp.read_text(errors="replace")))


def _check_disk(path: str, threshold_pct: int) -> bool:
    """Retourne True si l'utilisation disk est SOUS le seuil (service OK)."""
    import shutil

    usage = shutil.disk_usage(path)
    pct = int(usage.used / usage.total * 100)
    return pct < threshold_pct


def _check_gpu_temp(threshold: int) -> bool:
    """Retourne True si TOUTES les GPUs sont SOUS le seuil (service OK)."""
    r = subprocess.run(
        ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader"],
        capture_output=True,
        text=True,
        timeout=8,
    )
    if r.returncode != 0:
        return True  # pas de GPU = pas de problème GPU
    temps = [
        int(t.strip()) for t in r.stdout.strip().splitlines() if t.strip().isdigit()
    ]
    return all(t < threshold for t in temps)


def run_check(rule: dict) -> bool:
    """Retourne True si tout va bien (pas d'issue), False si problème détecté."""
    c = rule["check"]
    t = c["type"]
    if t == "port":
        return _check_port(c["host"], c["port"])
    if t == "http":
        return _check_http(c["url"])
    if t == "grep":
        return _check_grep(c["file"], c["pattern"])
    if t == "disk":
        return _check_disk(c["path"], c["threshold_pct"])
    if t == "gpu_temp":
        return _check_gpu_temp(c["threshold"])
    return True  # type inconnu = pas d'erreur


def apply_fix(rule: dict, dry_run: bool = False) -> str:
    fix = rule["fix"]
    t = fix["type"]
    if t == "systemd":
        cmd = [
            "systemctl",
            "--user" if fix.get("user") else "",
            fix["action"],
            fix["unit"],
        ]
        cmd = [c for c in cmd if c]
    elif t == "shell":
        cmd = ["bash", "-c", fix["cmd"].replace("~", str(Path.home()))]
    else:
        return f"type fix inconnu: {t}"

    if dry_run:
        return f"[DRY] {' '.join(cmd)}"

    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return "ok" if r.returncode == 0 else f"error: {r.stderr[:120]}"


def main():
    args = sys.argv[1:]
    mode = args[0] if args else "scan"
    as_json = "--json" in args
    dry_run = "--dry-run" in args

    kb = json.loads(KB_PATH.read_text())
    issues = []

    for rule in kb["rules"]:
        ok = run_check(rule)
        if not ok:
            issues.append(
                {
                    "id": rule["id"],
                    "description": rule["description"],
                    "severity": rule.get("severity", "medium"),
                    "fix": rule["fix"],
                }
            )

    if as_json:
        print(json.dumps({"issues": issues, "total": len(issues)}, indent=2))
        return 0

    if not issues:
        print("✅ Auto-debug : aucune issue détectée")
        return 0

    print(f"⚠️  {len(issues)} issue(s) détectée(s):")
    for iss in issues:
        sev_icon = "🔴" if iss["severity"] == "critical" else "🟡"
        print(f"  {sev_icon} [{iss['id']}] {iss['description']}")

    if mode == "fix":
        print("\n🔧 Application des fixes...")
        for iss in issues:
            result = apply_fix({"fix": iss["fix"]}, dry_run=dry_run)
            print(f"  [{iss['id']}] {result}")

    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
