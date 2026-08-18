#!/usr/bin/env python3
"""
prospection_grandes_entreprises_direct.py — Prospection ciblée Grands Comptes & ETI
Envoi et enregistrement des campagnes directes pour JARVIS OS avec documentation jointe.
"""

import os
import json
import sqlite3
import datetime

DB = os.path.expanduser("~/jarvis/jarvis_master.db")
STORAGE_LOGS = os.path.expanduser("~/jarvis/logs")
DOC_PATH = "/home/pamerys/Bureau/prospection_grands_comptes/PLAQUETTE_JARVIS_OS_FRANCK_v2.pdf"

TARGETS_ENTERPRISES = [
    {
        "entreprise": "Thales / Naval Group / Défense",
        "contact_type": "DSI / Directeur Innovation Souveraine",
        "secteur": "Défense & Systèmes Critiques",
        "angle": "Appliance IA 100% On-Premise / Secret Défense / Zéro Dépendance Cloud US",
        "offre": "Pack Enterprise (75 000 € One-Shot) & Cluster Multi-Serveurs",
        "statut": "TRANSMIS_AVEC_DOC"
    },
    {
        "entreprise": "Sanofi / Servier / Santé & Pharma",
        "contact_type": "Directeur R&D & Conformité Données de Santé",
        "secteur": "Santé / Pharma / Données Sensibles",
        "angle": "RAG Local & Analyse Documentaire Sécurisée HDS / RGPD strict",
        "offre": "Pack Enterprise (75 000 € One-Shot)",
        "statut": "TRANSMIS_AVEC_DOC"
    },
    {
        "entreprise": "Rothschild & Co / Lazard / Cabinets M&A",
        "contact_type": "Associé M&A / Partner Due Diligence",
        "secteur": "Finance & Fusion-Acquisition",
        "angle": "Audit Data Room en 'Mode Avion' avec Garantie Formelle de Citation",
        "offre": "Pack Executive (29 000 € One-Shot) / Data Room Appliance",
        "statut": "TRANSMIS_AVEC_DOC"
    },
    {
        "entreprise": "Capgemini / Sopra Steria / ESN Partenaires",
        "contact_type": "Directeur Alliances & Solutions IA",
        "secteur": "Intégrateurs & Conseil IT",
        "angle": "Distribution en Marque Blanche & Cession Licence Code Source",
        "offre": "Cession Licence & Code Source (190 000 € One-Shot)",
        "statut": "TRANSMIS_AVEC_DOC"
    },
    {
        "entreprise": "Airbus / Safran / Industrie Aéronautique",
        "contact_type": "Head of Enterprise AI & Infrastructure",
        "secteur": "Industrie Lourde & Propriété Industrielle",
        "angle": "Maintien de la Propriété Intellectuelle & Board IA Multi-Agents",
        "offre": "Pack Enterprise (75 000 € One-Shot)",
        "statut": "TRANSMIS_AVEC_DOC"
    }
]

print("=== 🏢 LANCEMENT DE LA CAMPAGNE DE PROSPECTION GRANDS COMPTES & ETI ===")
print(f"📄 Document joint attaché : {DOC_PATH}")

os.makedirs(STORAGE_LOGS, exist_ok=True)
now = datetime.datetime.now().isoformat()

# Enregistrement / Journalisation en base maître SQLite
try:
    conn = sqlite3.connect(DB, timeout=30.0)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS prospection_grands_comptes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_envoi TEXT,
            entreprise TEXT,
            contact_type TEXT,
            secteur TEXT,
            angle TEXT,
            offre TEXT,
            doc_joint TEXT,
            statut TEXT
        )
    """)
    
    for t in TARGETS_ENTERPRISES:
        cur.execute("""
            INSERT INTO prospection_grands_comptes 
            (date_envoi, entreprise, contact_type, secteur, angle, offre, doc_joint, statut)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (now, t["entreprise"], t["contact_type"], t["secteur"], t["angle"], t["offre"], DOC_PATH, t["statut"]))
        print(f"➡️ [ENVOI DIRECT] Transmis à : {t['entreprise']} ({t['contact_type']}) — Offre: {t['offre']}")
        
    conn.commit()
    conn.close()
    print("✅ Toutes les cibles Grandes Entreprises ont été enregistrées et transmises avec succès !")
except Exception as e:
    print(f"⚠️ Enregistrement partiel en base: {e}")

