#!/usr/bin/env python3
"""Génère l'INDEX DE ROUTAGE du groupe JARVIS : ports en écoute → process → service
systemd → filiale. Déterministe (ss + /proc + systemctl), 0 LLM. Ré-exécutable.

Usage: python3 scripts/build-routing-index.py [--json-only]
Sortie: audit/ROUTING_INDEX.json (+ table lisible sur stdout).
"""

import json
import os
import re
import subprocess
import sys

OUT = os.path.expanduser("~/jarvis/audit/ROUTING_INDEX.json")

# Câblage connu : port → (service logique, filiale) — enrichit l'auto-détection
KNOWN = {
    1234: ("LM Studio M1", "NEURAL"),
    11434: ("Ollama (local+cloud)", "NEURAL"),
    18800: ("hub LLM chat_proxy", "NEURAL"),
    18802: ("ccr (claude-code-router)", "NEURAL"),
    9743: ("Whisper STT", "VOICE"),
    9201: ("BrowserOS MCP", "WEB"),
    9108: ("BrowserOS CDP", "WEB"),
    9222: ("Chrome CDP (jarvis-cdp)", "WEB"),
    9001: ("Antigravity DEV CDP", "WEB"),
    9011: ("Antigravity PROD CDP", "WEB"),
    7788: ("hub Mirra FastAPI", "CONTENT"),
    5432: ("PostgreSQL", "DATA"),
    6379: ("Redis", "DATA"),
    5678: ("n8n", "DATA"),
    9100: ("node_exporter metrics", "OPS"),
}


def listening_ports():
    """→ {port: pid} via ss -tlnp."""
    out = subprocess.run(["ss", "-tlnpH"], capture_output=True, text=True).stdout
    res = {}
    for line in out.splitlines():
        m_port = re.search(r":(\d+)\s", line)
        m_pid = re.search(r"pid=(\d+)", line)
        if m_port:
            res[int(m_port.group(1))] = int(m_pid.group(1)) if m_pid else None
    return res


def proc_name(pid):
    if not pid:
        return None
    try:
        with open(f"/proc/{pid}/comm") as f:
            return f.read().strip()
    except Exception:
        return None


def systemd_unit(pid):
    if not pid:
        return None
    try:
        with open(f"/proc/{pid}/cgroup") as f:
            txt = f.read()
        m = re.search(r"/([\w@.-]+\.service)", txt)
        return m.group(1) if m else None
    except Exception:
        return None


def build():
    ports = listening_ports()
    rows = []
    for port in sorted(ports):
        pid = ports[port]
        svc, branch = KNOWN.get(port, (None, None))
        rows.append(
            {
                "port": port,
                "pid": pid,
                "process": proc_name(pid),
                "unit": systemd_unit(pid),
                "service": svc,
                "filiale": branch,
            }
        )
    return rows


def main():
    rows = build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(
            {"generated": "deterministic", "count": len(rows), "routes": rows},
            f,
            ensure_ascii=False,
            indent=2,
        )
    if "--json-only" not in sys.argv:
        print(f"=== INDEX DE ROUTAGE JARVIS — {len(rows)} ports → {OUT} ===")
        named = [r for r in rows if r["service"] or r["unit"]]
        for r in named:
            print(
                f"  :{r['port']:<6} {r.get('filiale') or '?':<8} "
                f"{r.get('service') or r.get('unit') or r.get('process') or '?'}"
            )
        print(f"  (+ {len(rows) - len(named)} ports non mappés)")


if __name__ == "__main__":
    main()
