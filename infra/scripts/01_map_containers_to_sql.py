#!/usr/bin/env python3
"""
JARVIS — Phase 1 : Cartographie containers → jarvis_endpoints + jarvis_agents
Exécuter : python3 /home/pamerys/jarvis/infra/scripts/01_map_containers_to_sql.py
"""

import subprocess
import json
import sqlite3
import sys
from datetime import datetime

DB = "/home/pamerys/jarvis/data/jarvis.db"
NODE = "M1"

SENSITIVE_KEYWORDS = {
    "trading",
    "linkedin",
    "whatsapp",
    "codex",
    "omega",
    "lumen",
    "master",
    "production",
    "integrity",
    "valise",
    "postgres",
    "redis",
}


def get_containers():
    out = subprocess.check_output(
        ["docker", "inspect"]
        + subprocess.check_output(["docker", "ps", "-q"], text=True).split(),
        text=True,
    )
    return json.loads(out)


def classify(name):
    n = name.lower().lstrip("/")
    return 1 if any(k in n for k in SENSITIVE_KEYWORDS) else 0


def extract(c):
    name = c["Name"].lstrip("/")
    image = c["Config"]["Image"]
    nets = c["NetworkSettings"]["Networks"]
    ports_map = c["NetworkSettings"]["Ports"] or {}

    first_net = next(iter(nets), "host")
    internal_ip = (
        nets[first_net].get("IPAddress", "") if first_net != "host" else "127.0.0.1"
    )
    first_port = None
    for pspec, binds in ports_map.items():
        try:
            first_port = int(pspec.split("/")[0])
            break
        except Exception:
            pass

    return {
        "id": name,
        "name": name,
        "image": image,
        "network": first_net,
        "internal_ip": internal_ip or "127.0.0.1",
        "port": first_port,
        "is_sensitive": classify(name),
        "networks_raw": json.dumps(list(nets.keys())),
    }


def main():
    try:
        raw = get_containers()
    except Exception as e:
        print(f"[ERR] docker inspect failed: {e}", file=sys.stderr)
        sys.exit(1)

    con = sqlite3.connect(DB)
    cur = con.cursor()
    now = datetime.utcnow().isoformat()
    inserted_ep = inserted_ag = 0

    for c in raw:
        d = extract(c)
        # jarvis_endpoints
        cur.execute(
            """
            INSERT OR IGNORE INTO jarvis_endpoints
              (id, name, type, host, port, network, internal_ip,
               is_sensitive, has_buffer, auth_required, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
            (
                d["id"],
                d["name"],
                "container",
                "127.0.0.1",
                d["port"],
                d["network"],
                d["internal_ip"],
                d["is_sensitive"],
                0,
                "none",
                now,
            ),
        )
        inserted_ep += cur.rowcount

        # jarvis_agents (tier 3 par défaut, à affiner manuellement)
        tier = (
            1
            if "master" in d["id"] or "orchestr" in d["id"]
            else 2
            if d["is_sensitive"]
            else 3
        )
        cur.execute(
            """
            INSERT OR IGNORE INTO jarvis_agents
              (id, name, node, container_name, tier, status, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?)
        """,
            (d["id"], d["name"], NODE, d["id"], tier, "active", now, now),
        )
        inserted_ag += cur.rowcount

    con.commit()
    con.close()
    total = len(raw)
    print(
        f"[OK] {total} containers scannés | {inserted_ep} endpoints insérés | {inserted_ag} agents insérés"
    )
    # Rapport sensibilité
    sensitive = [extract(c)["id"] for c in raw if classify(c["Name"].lstrip("/"))]
    print(f"[!] Containers sensibles ({len(sensitive)}) : {', '.join(sensitive)}")


if __name__ == "__main__":
    main()
