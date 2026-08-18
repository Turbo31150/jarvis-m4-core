#!/usr/bin/env python3
"""
JARVIS OMEGA — Relais & Bridge Réseau Direct M6 <-> LM Studio M1
Gère le routage et le tunnel automatique pour le câble direct M6 <-> M1.
"""

import sqlite3
import os
import json

DB_PATH = os.path.expanduser("~/jarvis/jarvis_master.db")
# WAL : un seul écrivain à la fois sur une base très sollicitée,
# il faut attendre au lieu d'échouer sur "database is locked".
conn = sqlite3.connect(DB_PATH, timeout=120)
conn.execute("PRAGMA busy_timeout=120000")
cur = conn.cursor()

# 1. Enregistrement du lien direct M6 <-> M1 dans la base des nœuds du cluster
cur.execute("""
INSERT INTO cluster_nodes (ip, hostname, status, role, services)
VALUES ('10.42.0.85', 'M1-Direct-Cable', 'STANDBY_CABLE', 'LM Studio High-Power 6-GPU Server', 'lmstudio:1234')
ON CONFLICT(ip) DO UPDATE SET
    hostname=excluded.hostname,
    status='STANDBY_CABLE',
    role=excluded.role,
    services=excluded.services,
    last_ping=datetime('now')
""")

# 2. Configuration du domino de pont réseau direct M6 <-> M1
cur.execute(
    """
INSERT INTO domino_chains (serie, verdict, danger, steps, backend, next_serie, logique)
VALUES (?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(serie) DO UPDATE SET
    verdict=excluded.verdict,
    steps=excluded.steps,
    backend=excluded.backend,
    logique=excluded.logique
""",
    (
        "jarvis-m6-m1-direct-cable-bridge",
        "enhanced",
        "none",
        json.dumps(
            [
                "m6.network.probe.m1",
                "cable.direct.link.verify",
                "m1.lmstudio.auto_detect",
                "route.llm.priority.update",
            ]
        ),
        "orchestrator",
        "jarvis-m6-node-exploitation",
        "Bridge & Câblage Réseau Direct M6 <-> M1 (10.42.0.85 / 192.168.0.10) : Inférence LM Studio 6-GPU",
    ),
)

conn.commit()
conn.close()

print(
    "✅ Câblage direct M6 <-> M1 (LM Studio 6-GPU) enregistré dans le cluster et prêt à s'activer dès l'allumage du port M1 !"
)
