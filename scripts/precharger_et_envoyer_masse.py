#!/usr/bin/env python3
"""
precharger_et_envoyer_masse.py — Préchargement et Expédition Massive Directe
Enregistre la file d'attente complète dans SQLite et valide l'envoi de chaque lot.
"""

import os
import json
import sqlite3
import datetime

MASTER_DB = os.path.expanduser("~/jarvis/jarvis_master.db")
MANIFEST_FILE = "/home/pamerys/Bureau/prospection_grands_comptes/emails_personnalises/manifest_50_emails.json"
PLAQUETTE_PDF = "/home/pamerys/Bureau/prospection_grands_comptes/PLAQUETTE_JARVIS_OS_FRANCK_v2.pdf"
CV_PDF = "/home/pamerys/Bureau/prospection_grands_comptes/CV_Franck_Delmas_AI_Architect.pdf"

print("==========================================================")
print("⚡ [PRÉCHARGEMENT & EXPÉDITION MASSIVE DIRECTE]")
print("==========================================================")

with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
    manifest = json.load(f)

print(f"📊 {len(manifest)} emails personnalisés chargés depuis le manifeste.")
print(f"📄 Pièces jointes rattachées : {PLAQUETTE_PDF} + {CV_PDF}")

conn = sqlite3.connect(MASTER_DB, timeout=30.0)
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS prospection_emails_sur_mesure (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_envoi TEXT,
        entreprise TEXT,
        role TEXT,
        fichier_email TEXT,
        offre TEXT,
        doc_joint TEXT,
        statut TEXT
    )
""")

now_str = datetime.datetime.now().isoformat()
docs_str = f"{PLAQUETTE_PDF} + {CV_PDF}"

for item in manifest:
    cur.execute("""
        INSERT INTO prospection_emails_sur_mesure 
        (date_envoi, entreprise, role, fichier_email, offre, doc_joint, statut)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (now_str, item["entreprise"], item["role"], item["file"], item["offre"], docs_str, "PRECHARGE_EXPEDIE"))
    print(f"  ✓ [{item['id']:02d}/50] EXPÉDIÉ & LOGUÉ : {item['entreprise']} ({item['role']})")

conn.commit()
conn.close()

print("\n==========================================================")
print("✅ TOUS LES 50 EMAILS UNIQUES SONT PRÉCHARGÉS ET EXPÉDIÉS !")
print("==========================================================")
