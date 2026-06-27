#!/usr/bin/env python3
"""
mindmap.py — Carte mentale JARVIS (composants + connexions)
Usage: python3 mindmap.py [--rebuild] [--update-services] [--show]
"""

import argparse
import json
import os
import sqlite3
import subprocess
from datetime import datetime

DB_PATH = "/home/pamerys/jarvis/jarvis_master.db"

KNOWN_NODES = [
    # CLI / core
    {"node": "jarvis-master-cli", "type": "script", "path": "/home/pamerys/jarvis/cli/jarvis_master.py",
     "machine": "OL1", "connects_to": ["jarvis_master.db", "loop-monitor", "disk-index"],
     "description": "CLI principal JARVIS — todo + dispatcher"},
    {"node": "loop-monitor", "type": "service", "path": "/home/pamerys/jarvis/cli/loop_monitor.py",
     "machine": "OL1", "connects_to": ["jarvis_master.db", "jarvis-master.service"],
     "description": "Surveille la boucle autonome JARVIS"},
    {"node": "disk-index", "type": "script", "path": "/home/pamerys/jarvis/cli/disk_index.py",
     "machine": "OL1", "connects_to": ["jarvis_master.db"],
     "description": "Index fichiers multi-machines dans disk_index table"},
    {"node": "monitoring-server", "type": "service", "path": "/home/pamerys/jarvis/monitoring/",
     "machine": "OL1", "connects_to": ["jarvis_master.db", "node-agent"],
     "description": "Serveur monitoring cluster"},
    {"node": "node-agent", "type": "agent", "path": "/home/pamerys/jarvis/infra/",
     "machine": "M1/M2", "connects_to": ["monitoring-server"],
     "description": "Agent nœud distant pour reporting cluster"},
    # Agents
    {"node": "openclaw", "type": "service", "path": "/home/pamerys/jarvis/",
     "machine": "OL1", "connects_to": ["cowork-dispatcher", "jarvis_master.db"],
     "description": "Sandbox agents OpenClaw spécialisés"},
    {"node": "cowork-dispatcher", "type": "service", "path": "/home/pamerys/jarvis-cowork/",
     "machine": "OL1", "connects_to": ["cowork_engine.db", "lm-studio", "openclaw"],
     "description": "Dispatcher tâches JARVIS Cowork vers agents"},
    {"node": "antigravity", "type": "service", "path": "/home/pamerys/jarvis/antigravity_heavy_tasks/",
     "machine": "OL1", "connects_to": ["jarvis_master.db", "m2-lmstudio"],
     "description": "Tâches lourdes déléguées (heavy tasks)"},
    # LLM backends
    {"node": "lm-studio", "type": "model", "path": "http://192.168.1.85:1234",
     "machine": "M1", "connects_to": ["cowork-dispatcher", "antigravity", "jarvis-ai-proxy"],
     "description": "LM Studio M1 — qwen3.5-35b, claude-opus-distilled"},
    {"node": "m2-lmstudio", "type": "model", "path": "http://192.168.1.26:1234",
     "machine": "M2", "connects_to": ["cowork-dispatcher", "antigravity"],
     "description": "LM Studio M2 — qwen3.5-35b, deepseek-r1"},
    {"node": "ollama", "type": "model", "path": "http://127.0.0.1:11434",
     "machine": "OL1", "connects_to": ["lm-ask"],
     "description": "Ollama local — gemma3:4b, llama3.2"},
    {"node": "lm-ask", "type": "script", "path": "/home/pamerys/jarvis/scripts/lm-ask.sh",
     "machine": "OL1", "connects_to": ["lm-studio", "m2-lmstudio", "ollama"],
     "description": "Proxy shell 1-shot vers backends LLM avec fallback"},
    {"node": "jarvis-ai-proxy", "type": "service", "path": "/etc/systemd/system/jarvis-ai-proxy.service",
     "machine": "OL1", "connects_to": ["lm-studio", "m2-lmstudio", "ollama"],
     "description": "Proxy HTTP unifié tous modèles LLM"},
    # Databases
    {"node": "jarvis_master.db", "type": "db", "path": "/home/pamerys/jarvis/jarvis_master.db",
     "machine": "OL1", "connects_to": [],
     "description": "DB principale JARVIS — tasks, pipeline_log, disk_index, mindmap"},
    {"node": "cowork_engine.db", "type": "db", "path": "/home/pamerys/jarvis/cowork_engine.db",
     "machine": "OL1", "connects_to": ["cowork-dispatcher"],
     "description": "DB moteur cowork — jobs, résultats agents"},
    {"node": "jarvis_web_nav.db", "type": "db", "path": "/home/pamerys/jarvis/data/jarvis_web_nav.db",
     "machine": "OL1", "connects_to": ["jarvis-chrome-cdp"],
     "description": "DB navigation web JARVIS"},
    # Services systemd JARVIS
    {"node": "jarvis-master.service", "type": "service", "path": "/etc/systemd/system/jarvis-master.service",
     "machine": "OL1", "connects_to": ["jarvis-master-cli", "jarvis_master.db"],
     "description": "Service systemd boucle autonome JARVIS"},
    {"node": "jarvis-openclaw.service", "type": "service", "path": "/etc/systemd/system/jarvis-openclaw.service",
     "machine": "OL1", "connects_to": ["openclaw"],
     "description": "Service systemd agents OpenClaw"},
    {"node": "jarvis-orchestrator.service", "type": "service", "path": "/etc/systemd/system/jarvis-orchestrator.service",
     "machine": "OL1", "connects_to": ["cowork-dispatcher", "lm-studio"],
     "description": "Orchestrateur global JARVIS"},
    {"node": "jarvis-pulse.service", "type": "service", "path": "/etc/systemd/system/jarvis-pulse.service",
     "machine": "OL1", "connects_to": ["jarvis_master.db", "monitoring-server"],
     "description": "Heartbeat cluster JARVIS"},
    {"node": "jarvis-watchdog.service", "type": "service", "path": "/etc/systemd/system/jarvis-watchdog.service",
     "machine": "OL1", "connects_to": ["jarvis-master.service", "jarvis_master.db"],
     "description": "Watchdog redémarre services JARVIS en cas de crash"},
    {"node": "jarvis-score-updater.service", "type": "service", "path": "/etc/systemd/system/jarvis-score-updater.service",
     "machine": "OL1", "connects_to": ["jarvis_master.db"],
     "description": "Met à jour le score santé JARVIS"},
    {"node": "jarvis-chrome-cdp.service", "type": "service", "path": "/etc/systemd/system/jarvis-chrome-cdp.service",
     "machine": "OL1", "connects_to": ["jarvis_web_nav.db"],
     "description": "Chrome DevTools Protocol pour navigation web JARVIS"},
    {"node": "jarvis-ia-web-mcp.service", "type": "service", "path": "/etc/systemd/system/jarvis-ia-web-mcp.service",
     "machine": "OL1", "connects_to": ["jarvis-ai-proxy", "jarvis_web_nav.db"],
     "description": "MCP web IA JARVIS"},
    {"node": "health-patrol.service", "type": "service", "path": "/etc/systemd/system/health-patrol.service",
     "machine": "OL1", "connects_to": ["jarvis_master.db", "monitoring-server"],
     "description": "Patrouille santé cluster"},
    {"node": "nav-recorder.service", "type": "service", "path": "/etc/systemd/system/nav-recorder.service",
     "machine": "OL1", "connects_to": ["jarvis_web_nav.db"],
     "description": "Enregistreur navigation web"},
]

def init_db(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS mindmap (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      node TEXT UNIQUE,
      type TEXT,
      path TEXT,
      machine TEXT,
      status TEXT,
      connects_to TEXT,
      description TEXT,
      last_seen TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_mindmap_node ON mindmap(node);
    CREATE INDEX IF NOT EXISTS idx_mindmap_type ON mindmap(type);
    """)
    conn.commit()

def get_service_status(service_name):
    try:
        r = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True, text=True, timeout=3
        )
        return r.stdout.strip()  # active / inactive / failed / unknown
    except Exception:
        return "unknown"

def rebuild(conn, update_services=True):
    now = datetime.utcnow().isoformat()
    for node in KNOWN_NODES:
        status = "unknown"
        if update_services and node["type"] == "service":
            svc = node["node"] if node["node"].endswith(".service") else node["node"] + ".service"
            status = get_service_status(svc)
        elif node["type"] in ("model", "script", "db", "agent"):
            path = node["path"]
            if path.startswith("http"):
                status = "unknown"  # require network check
            elif os.path.exists(path):
                status = "active"
            else:
                status = "inactive"

        conn.execute("""
            INSERT INTO mindmap (node, type, path, machine, status, connects_to, description, last_seen)
            VALUES (?,?,?,?,?,?,?,?)
            ON CONFLICT(node) DO UPDATE SET
              type=excluded.type, path=excluded.path, machine=excluded.machine,
              status=excluded.status, connects_to=excluded.connects_to,
              description=excluded.description, last_seen=excluded.last_seen
        """, (
            node["node"], node["type"], node["path"], node["machine"],
            status, json.dumps(node["connects_to"]),
            node["description"], now
        ))
    conn.commit()
    return len(KNOWN_NODES)

def show(conn):
    rows = conn.execute("SELECT node, type, machine, status, connects_to, description FROM mindmap ORDER BY type, node").fetchall()
    print(f"{'NODE':<35} {'TYPE':<10} {'MACHINE':<8} {'STATUS':<10} DESCRIPTION")
    print("-" * 110)
    for r in rows:
        cto = json.loads(r[4]) if r[4] else []
        print(f"{r[0]:<35} {r[1]:<10} {r[2]:<8} {r[3]:<10} {r[5]}")

def main():
    parser = argparse.ArgumentParser(description="JARVIS Mindmap")
    parser.add_argument("--rebuild", action="store_true", help="Recrée tous les nœuds")
    parser.add_argument("--update-services", action="store_true", help="Vérifie statut systemd")
    parser.add_argument("--show", action="store_true", help="Affiche la carte")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    if args.rebuild or not conn.execute("SELECT COUNT(*) FROM mindmap").fetchone()[0]:
        n = rebuild(conn, update_services=args.update_services)
        print(f"{n} nœuds insérés/mis à jour")

    if args.show:
        show(conn)

    conn.close()

if __name__ == "__main__":
    main()
