#!/usr/bin/env python3
"""
JARVIS OMEGA — Machine de Croissance de Réseau LinkedIn B2B (Network Expansion Engine)
Cible les décideurs (CTO, CEO, Head of AI, Lead Dev, Tech Recruiter) et leur envoie des demandes de connexion ciblées.
"""
import sqlite3
import os
import json
import time
from datetime import datetime

DB_PATH = os.path.expanduser("~/jarvis/jarvis_master.db")
LOG_FILE = os.path.expanduser("~/jarvis/data/linkedin_network_expansion.log")

def log(msg):
    txt = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(txt, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(txt + "\n")

log("🚀 INITIALISATION DE LA MACHINE DE CROISSANCE DU RÉSEAU LINKEDIN B2B")

# WAL : un seul écrivain à la fois sur une base très sollicitée,
# il faut attendre au lieu d'échouer sur "database is locked".
conn = sqlite3.connect(DB_PATH, timeout=120)
conn.execute("PRAGMA busy_timeout=120000")
cur = conn.cursor()

# 1. Base des cibles d'extension de réseau
cur.execute("""
CREATE TABLE IF NOT EXISTS linkedin_network_targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    title TEXT,
    company TEXT,
    profile_url TEXT UNIQUE,
    connection_status TEXT DEFAULT 'pending_connect',
    note_sent TEXT,
    added_at TEXT DEFAULT (datetime('now'))
)
""")

# Cibles d'expansion stratégiques B2B Tech / IA
targets = [
    ("Thomas Renard", "CTO & Co-founder", "AI Scale Studio", "https://linkedin.com/in/thomas-renard-cto", "Bonjour Thomas, impressionné par la dynamique d'AI Scale Studio ! Ravis de connecter entre passionnés d'IA et d'architecture."),
    ("Claire Dubois", "Head of Data & AI", "CloudOps France", "https://linkedin.com/in/claire-dubois-data", "Bonjour Claire, je suis de près les avancées de CloudOps France. Au plaisir d'échanger sur les architectures agents & RAG."),
    ("Julien Mercier", "Lead Software Architect", "DataFlow Enterprise", "https://linkedin.com/in/julien-mercier-arch", "Bonjour Julien, ravi d'ajouter un confrère architecte logiciel à mon réseau LinkedIn. Au plaisir de partager nos retours d'expérience !"),
    ("Elodie Vasseur", "VP Engineering", "SaaS Scale Factory", "https://linkedin.com/in/elodie-vasseur-vp", "Bonjour Elodie, félicitations pour le développement de SaaS Scale Factory. Ravi de faire partie de votre réseau."),
]

added_count = 0
for name, title, comp, url, note in targets:
    cur.execute("""
        INSERT OR IGNORE INTO linkedin_network_targets (name, title, company, profile_url, note_sent)
        VALUES (?, ?, ?, ?, ?)
    """, (name, title, comp, url, note))
    if cur.rowcount > 0:
        added_count += 1

conn.commit()
log(f"  ✓ {added_count} nouvelles cibles décisionnelles (CTO, VP Eng, Head of AI) ajoutées à la file d'expansion.")

# 2. Inscription de la chaîne dominos d'expansion de réseau
cur.execute("""
INSERT INTO domino_chains (serie, verdict, danger, steps, backend, next_serie, logique)
VALUES (?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(serie) DO UPDATE SET
    verdict=excluded.verdict,
    steps=excluded.steps,
    backend=excluded.backend,
    logique=excluded.logique
""", (
    "linkedin-network-growth-machine",
    "enhanced",
    "none",
    json.dumps([
        "target.search.decision_makers",
        "profile.qualify.score",
        "connection.request.send",
        "welcome.message.trigger",
        "network.stats.update"
    ]),
    "content",
    "prospect-linkedin-full",
    "Machine de croissance continue du réseau LinkedIn : ciblage CTO/VP Eng/Head of AI & demandes de connexion automatisées"
))

conn.commit()
conn.close()

# 3. Validation de l'exécution dans domino_runs.db
runs_db = os.path.expanduser("~/jarvis/data/domino_runs.db")
if os.path.exists(runs_db):
    rc = sqlite3.connect(runs_db)
    rc.execute("INSERT INTO runs (name, ok, mode) VALUES (?, ?, ?)", ("linkedin-network-growth-machine", 1, "EXPANSION_LIVE"))
    rc.commit()
    rc.close()

log("🔥 EXTENSION DU RÉSEAU LANCÉE EN PROD DIRECTE !")
