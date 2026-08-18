#!/usr/bin/env python3
"""jv-registry-build — registre unique de l'entreprise JARVIS OS (0 token).

Lit l'état réel (docker + systemd + ports écoutés), mappe chaque unité vers la
nomenclature cible jv-<dept>-<unite> (cf docs/CDC_ARCHITECTURE_ENTREPRISE.md) et
écrit ~/jarvis/orchestrator/jv_registry.json. Non destructif : ne renomme rien.
"""

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

OUT = Path.home() / "jarvis" / "orchestrator" / "jv_registry.json"

# Mapping nom_actuel (regex) -> (dept, unite). Source: INDEX_CABLAGE_ENTREPRISE.md
RULES = [
    (
        r"whisper|voice|wakeword|ai-proxy|llm-monitor|openclaw|browseros|ia-web|ollama|lmstudio|lm-studio|ccr|chat-proxy|lumen\b|antigravity|chrome-cdp|gemma",
        "ia",
    ),
    (
        r"jarvis-master|cowork|jarvis-orchestrator|omega-bridge|watchdog|health-patrol|task-auto|task-executor|queue-worker|domino|pipeline|score|cascade-ingest|mcp-sse|jarvis-api",
        "dg",
    ),
    (
        r"redis|postgres|\bpg\b|bibliotheque-db|jarvis-monitor|jarvis-sre|integrity|gpu-monitor|gpu-oc|cpu-perf|jarvis-docs|jarvis-pulse|prometheus|alerting|sql-bridge|backup|log-rotate|session-|jarvis-share|cluster-mount|sync-config|fileserver|maintenance|autoheal|health-check|hub-healthcheck|process-monitor|zombie-reaper",
        "infra",
    ),
    (
        r"n8n|webhook|whatsapp|linkedin|commander|callagent|call-agent|telegram|os-pwa|jarvis-ws",
        "front",
    ),
    (r"biblioth|alkymia|lumen-token|library|feeder|production|mirra", "studio"),
    (r"trading|finance", "finance"),
    (r"valise", "log"),
]
PLAGES = {
    "dg": "7700-7799",
    "infra": "6300-6399/5400-5499/9100-9199",
    "ia": "9700-9799",
    "front": "5600-5699+5678",
    "studio": "3000-3099/5000-5099",
    "finance": "8200-8299",
    "log": "18800-18899",
}


def sh(cmd):
    try:
        return subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=15
        ).stdout
    except Exception:
        return ""


def dept_of(name):
    for rx, dept in RULES:
        if re.search(rx, name, re.I):
            return dept
    return "unassigned"


def canon(name, dept):
    u = re.sub(r"^(jarvis[-_]?|jv[-_]?)", "", name.lower())
    u = re.sub(r"[._]+", "-", u)
    u = re.sub(r"-(1|service|s)$", "", u)
    u = re.sub(r"[^a-z0-9-]", "-", u).strip("-") or "unit"
    return f"jv-{dept}-{u}"


def collect():
    units = {}
    # docker
    for line in sh(
        "docker ps -a --format '{{.Names}}|{{.Status}}|{{.Ports}}'"
    ).splitlines():
        p = line.split("|")
        if not p[0]:
            continue
        name, status = p[0], p[1] if len(p) > 1 else ""
        ports = p[2] if len(p) > 2 else ""
        m = re.search(r"0\.0\.0\.0:(\d+)", ports)
        dept = dept_of(name)
        units[("docker", name)] = {
            "nom_actuel": name,
            "type": "docker",
            "dept": dept,
            "nom_cible": canon(name, dept),
            "plage": PLAGES.get(dept, "?"),
            "port": int(m.group(1)) if m else None,
            "reseau_cible": f"jvnet-{dept}",
            "health_url": None,
            "etat": "up" if status.startswith("Up") else "down",
        }
    # systemd (system + user) jarvis-like
    for scope in ("", "--user"):
        out = sh(f"systemctl {scope} list-units --type=service --all --no-legend")
        for line in out.splitlines():
            m = re.match(r"[●\s]*([\w@.\-]+)\.service\s+\S+\s+(\w+)\s+(\w+)", line)
            if not m:
                continue
            svc, active = m.group(1), m.group(2)
            if not re.search(
                r"jarvis|lumen|whisper|ccr|antigravity|browseros|openclaw", svc, re.I
            ):
                continue
            if "failure-handler" in svc:
                continue
            dept = dept_of(svc)
            key = ("systemd-user" if scope else "systemd", svc)
            units[key] = {
                "nom_actuel": svc,
                "type": key[0],
                "dept": dept,
                "nom_cible": canon(svc, dept),
                "plage": PLAGES.get(dept, "?"),
                "port": None,
                "reseau_cible": f"jvnet-{dept}",
                "health_url": None,
                "etat": active,
            }
    return list(units.values())


def main():
    units = collect()
    by_dept = {}
    for u in units:
        by_dept.setdefault(u["dept"], []).append(u["nom_cible"])
    reg = {
        "version": "1.0",
        "generated": datetime.now(timezone.utc).isoformat(),
        "source": "docker+systemd+ss (deterministe, 0 token)",
        "cdc": "docs/CDC_ARCHITECTURE_ENTREPRISE.md",
        "plages": PLAGES,
        "count": len(units),
        "by_dept": {d: sorted(set(v)) for d, v in sorted(by_dept.items())},
        "units": sorted(units, key=lambda x: (x["dept"], x["nom_cible"])),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(reg, indent=2, ensure_ascii=False))
    print(f"[jv-registry] {len(units)} unites -> {OUT}")
    for d, v in reg["by_dept"].items():
        print(f"  {d:11} {len(v):2} unites")
    if any(u["dept"] == "unassigned" for u in units):
        print(
            "  ! unassigned:",
            [u["nom_actuel"] for u in units if u["dept"] == "unassigned"],
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
