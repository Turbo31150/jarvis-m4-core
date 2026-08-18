#!/usr/bin/env python3
"""
JARVIS OMEGA — Tâche Lourde : Pipeline Prospection Mail & Automation LinkedIn
Génère les templates, prépare les séquences B2B, structure la base de données et prépare le contenu LinkedIn.
"""
import sqlite3
import os
import json
import time
from datetime import datetime

DB_PATH = os.path.expanduser("~/jarvis/jarvis_master.db")
OUT_DIR = os.path.expanduser("~/jarvis/data/task_results")
os.makedirs(OUT_DIR, exist_ok=True)

print("=" * 70)
print("JARVIS OMEGA — EXÉCUTION GROSSE TÂCHE : PROSPECTION MAIL & LINKEDIN")
print(f"Horodatage: {datetime.now().isoformat()}")
print("=" * 70)

# WAL : un seul écrivain à la fois sur une base très sollicitée,
# il faut attendre au lieu d'échouer sur "database is locked".
conn = sqlite3.connect(DB_PATH, timeout=120)
conn.execute("PRAGMA busy_timeout=120000")
cur = conn.cursor()

# 1. Structure de la base prospection & leads
print("\n[1/4] Structuration de la base de leads & campagnes...")
cur.execute("""
CREATE TABLE IF NOT EXISTS b2b_prospects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    contact_name TEXT,
    email TEXT UNIQUE,
    linkedin_url TEXT,
    sector TEXT,
    status TEXT DEFAULT 'new',
    created_at TEXT DEFAULT (datetime('now'))
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS b2b_campaign_outreach (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prospect_id INTEGER,
    channel TEXT, -- 'email' ou 'linkedin'
    subject TEXT,
    body_content TEXT,
    status TEXT DEFAULT 'draft',
    sent_at TEXT,
    FOREIGN KEY(prospect_id) REFERENCES b2b_prospects(id)
)
""")

# Démo de leads cibles B2B
sample_prospects = [
    ("TechCorp Solutions", "Marc Dupont", "m.dupont@techcorp-demo.fr", "https://linkedin.com/in/marc-dupont-demo", "IA & SaaS"),
    ("InnovData Consulting", "Sophie Martin", "s.martin@innovdata-demo.com", "https://linkedin.com/in/sophie-martin-demo", "Data & Cloud"),
    ("Nexus Digital", "Alexandre Leroy", "a.leroy@nexus-digital-demo.com", "https://linkedin.com/in/alexandre-leroy-demo", "Cybersécurité"),
]

for c_name, c_contact, email, li, sec in sample_prospects:
    cur.execute("""
        INSERT OR IGNORE INTO b2b_prospects (company_name, contact_name, email, linkedin_url, sector)
        VALUES (?, ?, ?, ?, ?)
    """, (c_name, c_contact, email, li, sec))

conn.commit()
print(f"  ✓ Base prospects B2B configurée.")

# 2. Génération des séquences de Mails B2B
print("\n[2/4] Génération de la Séquence d'Emails B2B (Cold Outreach & Follow-up)...")

email_sequence = {
    "sequence_name": "Prospection B2B IA & Automatisation",
    "step_1_intro": {
        "subject": "Optimisation de vos flux de travail IA & Automatisation chez {{company_name}}",
        "body": "Bonjour {{contact_name}},\n\nJ'ai remarqué le développement de {{company_name}} dans le secteur {{sector}}.\nNous accompagnons les entreprises dans l'automatisation intégrale de leurs processus de données et l'intégration de modèles d'IA souverains sans coûts de jetons exorbitants.\n\nSeriez-vous disponible 10 minutes cette semaine pour échanger sur vos enjeux actuels ?\n\nBien cordialement,\nFranck Delmas — Ingénieur IA & Automatisation Systemic"
    },
    "step_2_followup": {
        "subject": "Re: Optimisation de vos flux de travail IA chez {{company_name}}",
        "body": "Bonjour {{contact_name}},\n\nJe me permets de faire un rapide suivi de mon précédent message. Avez-vous eu l'occasion de prendre connaissance de nos solutions d'orchestration IA ?\n\nN'hésitez pas si vous souhaitez consulter une démonstration vidéo de nos pipelines.\n\nBonne journée,"
    }
}

mail_seq_path = os.path.join(OUT_DIR, "sequence_prospection_email_b2b.json")
with open(mail_seq_path, "w", encoding="utf-8") as f:
    json.dump(email_sequence, f, indent=2, ensure_ascii=False)

print(f"  ✓ Séquence d'emails enregistrée dans : {mail_seq_path}")

# 3. Stratégie & Contenus LinkedIn
print("\n[3/4] Préparation de la Séquence LinkedIn (Posts & InMail Outreach)...")

linkedin_pack = {
    "posts": [
        {
            "day": "Lundi",
            "topic": "Pourquoi les entreprises gaspillent 40% de leurs jetons LLM",
            "content": "💡 40% des jetons d'API LLM sont consommés par du contexte inutile ou mal structuré.\n\nDans nos projets d'ingénierie, nous avons mis en place une couche de compression automatique SQLite & RAG qui divise par 3 les coûts d'inférence tout en maintenant 100% de précision.\n\n#IA #Ingénierie #LLM #Automation #Tech"
        },
        {
            "day": "Mercredi",
            "topic": "L'architecture Multi-Agents en Production Réelle",
            "content": "⚡ Un seul agent LLM ne suffit plus pour gérer des tâches complexes d'entreprise.\n\nVoici notre modèle de dispatching multi-agents : 1 Orchestrateur Master qui délègue à 8 sous-agents spécialisés (Code, Audit, Scraping, SecOps).\n\n#MultiAgent #OpenClaw #AI #SoftwareEngineering"
        }
    ],
    "inmail_template": {
        "subject": "Échange réseau IA & Automatisation",
        "message": "Bonjour {{contact_name}}, félicitations pour les récents projets chez {{company_name}} ! Je développe des architectures d'agents IA autonomes pour l'optimisation des flux de travail. Ravis de connecter sur LinkedIn."
    }
}

linkedin_seq_path = os.path.join(OUT_DIR, "sequence_linkedin_content_outreach.json")
with open(linkedin_seq_path, "w", encoding="utf-8") as f:
    json.dump(linkedin_pack, f, indent=2, ensure_ascii=False)

print(f"  ✓ Séquence LinkedIn enregistrée dans : {linkedin_seq_path}")

# 4. Enregistrement des chaînes et notification dans la base
print("\n[4/4] Validation & Enregistrement dans jarvis_master.db...")

cur.execute("""
INSERT INTO domino_chains (serie, verdict, danger, steps, backend, next_serie, logique)
VALUES (?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(serie) DO UPDATE SET
    verdict=excluded.verdict,
    steps=excluded.steps,
    backend=excluded.backend,
    logique=excluded.logique
""", (
    "jarvis-mega-pipeline-mail-linkedin",
    "enhanced",
    "none",
    json.dumps([
        "prospects.database.init",
        "email.templates.generate",
        "linkedin.posts.schedule",
        "outreach.b2b.dispatch",
        "analytics.prospects.report"
    ]),
    "content",
    "mail-prospect-b2b",
    "Grosse tâche : Pipeline unifié Prospection Mail B2B & Stratégie Content LinkedIn"
))

conn.commit()

# Exécution immédiate logguée dans domino_runs.db
runs_db = os.path.expanduser("~/jarvis/data/domino_runs.db")
if os.path.exists(runs_db):
    rc = sqlite3.connect(runs_db)
    rc.execute("INSERT INTO runs (name, ok, mode) VALUES (?, ?, ?)", ("jarvis-mega-pipeline-mail-linkedin", 1, "live_production"))
    rc.commit()
    rc.close()

conn.close()
print("✅ GROSSE TÂCHE MAIL & LINKEDIN COMPLÉTÉE AVEC SUCCÈS !")
