#!/usr/bin/env python3
"""
JARVIS OMEGA — Intégrateur Système des Workflows n8n (Mail & LinkedIn)
Inscrit les 3 workflows n8n dans la base maître et lie les déclencheurs au pipeline autonome.
"""
import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.expanduser("~/jarvis/jarvis_master.db")
# WAL : un seul écrivain à la fois sur une base très sollicitée,
# il faut attendre au lieu d'échouer sur "database is locked".
conn = sqlite3.connect(DB_PATH, timeout=120)
conn.execute("PRAGMA busy_timeout=120000")
cur = conn.cursor()

# 1. Enregistrement de la table n8n_workflows
cur.execute("""
CREATE TABLE IF NOT EXISTS n8n_workflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_name TEXT UNIQUE,
    file_path TEXT,
    trigger_interval TEXT,
    status TEXT DEFAULT 'active',
    last_run TEXT DEFAULT (datetime('now'))
)
""")

workflows = [
    ("Workflow 01 — Mail Surveillance & Auto-Response", "/home/pamerys/Workspaces/planning-app/n8n/workflow_01_mail_surveillance.json", "1 minute"),
    ("Workflow 02 — LinkedIn Auto-Engagement & Outreach", "/home/pamerys/Workspaces/planning-app/n8n/workflow_02_linkedin_automation.json", "5 minutes"),
    ("Workflow 03 — LinkedIn Network Expansion B2B", "/home/pamerys/Workspaces/planning-app/n8n/workflow_03_network_expansion.json", "1 heure"),
]

for name, path, interval in workflows:
    cur.execute("""
        INSERT INTO n8n_workflows (workflow_name, file_path, trigger_interval, status)
        VALUES (?, ?, ?, 'active')
        ON CONFLICT(workflow_name) DO UPDATE SET
            file_path=excluded.file_path,
            trigger_interval=excluded.trigger_interval,
            status='active'
    """, (name, path, interval))

# 2. Inscription dans domino_chains
cur.execute("""
INSERT INTO domino_chains (serie, verdict, danger, steps, backend, next_serie, logique)
VALUES (?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(serie) DO UPDATE SET
    verdict=excluded.verdict,
    steps=excluded.steps,
    backend=excluded.backend,
    logique=excluded.logique
""", (
    "jarvis-n8n-master-pipeline-mail-linkedin",
    "enhanced",
    "none",
    json.dumps([
        "n8n.workflow01.mail.trigger",
        "n8n.workflow02.linkedin.trigger",
        "n8n.workflow03.network.trigger",
        "system.logs.verify"
    ]),
    "orchestrator",
    "jarvis-mega-pipeline-mail-linkedin",
    "Super Pipeline n8n Unifié : Contrôle et Exécution Continue des 3 Workflows Mail et LinkedIn"
))

conn.commit()
conn.close()

print("✅ Les 3 Workflows n8n Mail & LinkedIn sont inscrits et intégrés dans jarvis_master.db !")
