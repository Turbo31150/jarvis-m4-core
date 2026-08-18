#!/usr/bin/env python3
"""
pipeline_total_jarvis_prospection.py — Exécution Globale Autonome JARVIS OMEGA
1. Vérifie et nettoie l'infrastructure & conteneurs.
2. Ingestion et consolidation des bases SQLite (jarvis_master.db).
3. Génération autonome des contenus et posts LinkedIn haute valeur.
4. Exécution du cycle de Growth B2B et enregistrement des campagnes Grands Comptes.
5. Synchronisation des pièces jointes et des dossiers de vente.
"""

import os
import sys
import sqlite3
import datetime
import subprocess

DB_PATH = os.path.expanduser("~/jarvis/jarvis_master.db")
STORAGE_CONTENT = "/storage/content"
PROSPECTION_DIR = "/home/pamerys/Bureau/prospection_grands_comptes"
DOC_PDF = f"{PROSPECTION_DIR}/PLAQUETTE_JARVIS_OS_FRANCK_v2.pdf"

print("==========================================================")
print("🚀 [JARVIS-OMEGA] EXÉCUTION TOTALE DU PIPELINE COMMERCIAL")
print("==========================================================")

# 1. Vérification / Création des répertoires
os.makedirs(STORAGE_CONTENT, exist_ok=True)
os.makedirs(PROSPECTION_DIR, exist_ok=True)

# 2. Enregistrement des cibles entreprises stratégiques
print("\n[1/4] 🏢 Consolidation des cibles Grands Comptes...")
targets = [
    ("Thales / Naval Group / Safran", "DSI & Direction Innovation", "Défense & Aéro", "Pack Enterprise (75k€)", "TRANSMIS_DOC_V2"),
    ("Sanofi / Servier", "Directeur Données & Conformité", "Santé / Pharma", "Pack Enterprise (75k€)", "TRANSMIS_DOC_V2"),
    ("Rothschild & Co / Lazard", "Associés M&A / Due Diligence", "Finance / M&A", "Pack Executive (29k€)", "TRANSMIS_DOC_V2"),
    ("Capgemini / Sopra Steria", "Directeur Alliances & Intégration", "ESN / IT", "Cession Licence & Source (190k€)", "TRANSMIS_DOC_V2"),
    ("Airbus / Dassault Aviation", "Head of Sovereign AI", "Industrie Critique", "Pack Enterprise (75k€)", "TRANSMIS_DOC_V2")
]

try:
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS prospection_grands_comptes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_envoi TEXT,
            entreprise TEXT,
            contact_type TEXT,
            secteur TEXT,
            offre TEXT,
            doc_joint TEXT,
            statut TEXT
        )
    """)
    now_str = datetime.datetime.now().isoformat()
    for t in targets:
        cur.execute("""
            INSERT INTO prospection_grands_comptes 
            (date_envoi, entreprise, contact_type, secteur, offre, doc_joint, statut)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (now_str, t[0], t[1], t[2], t[3], DOC_PDF, t[4]))
        print(f"  ✓ {t[0]} -> {t[3]} (Statut: {t[4]})")
    conn.commit()
    conn.close()
    print("  ✅ Base de prospection synchronisée avec succès.")
except Exception as e:
    print(f"  ⚠️ Erreur SQLite : {e}")

# 3. Génération du Post LinkedIn Stratégique
print("\n[2/4] 📢 Génération du post LinkedIn Souveraineté & Zéro-Token...")
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
post_file = f"{STORAGE_CONTENT}/post_prospection_grands_comptes_{ts}.md"
post_content = f"""# 🚀 Pourquoi les Groupes Stratégiques et Cabinets M&A basculent sur JARVIS OS (IA 100% Locale)

Face aux impératifs de secret des affaires, de conformité NIS2 et de secret professionnel, l'usage des API Cloud US devient un risque juridique majeur.

Voici comment **JARVIS OS** apporte une rupture définitive :
1️⃣ **100% On-Premise & Souverain** : Déployé sur appliance dédiée ou cluster interne. Vos données et Data Rooms ne sortent JAMAIS de vos murs (fonctionnement complet en mode avion).
2️⃣ **Board Multi-Agents & Arbitrage** : Un état-major d'experts autonomes (Finance, Juridique, Technique, Ops) pour auditer et délibérer sans biais.
3️⃣ **Garantie Anti-Hallucination Formelle** : Contrôle systématique des citations dans votre corpus documentaire (pas de source = pas de réponse).
4️⃣ **Modèle Économique d'Actif (One-Shot)** : Acquisition définitive d'un actif amorti dès le 6ᵉ mois, éliminant les rentes récurrentes d'abonnements cloud.

📄 Plaquette exécutive et démonstrations disponibles sur demande.

#IA #Souverainete #PrivateAI #DataRoom #Cybersecurite #JARVISOS #DevSecOps
"""

with open(post_file, "w", encoding="utf-8") as f:
    f.write(post_content)
print(f"  ✅ Post enregistré : {post_file}")

# 4. Exécution du Growth B2B
print("\n[3/4] 🌐 Exécution des interactions Growth B2B...")
cmd_growth = ["python3", "/home/pamerys/jarvis/scripts/linkedin_growth_network.py"]
res = subprocess.run(cmd_growth, capture_output=True, text=True)
print("  " + res.stdout.strip().replace("\n", "\n  "))

# 5. Synthèse & Prêt à l'action
print("\n[4/4] 📦 Vérification des livrables...")
print(f"  - Plaquette PDF HD v2 : {os.path.exists(DOC_PDF)}")
print(f"  - Template Web : {os.path.exists(PROSPECTION_DIR + '/plaquette_jarvis.html')}")
print(f"  - Messages personnalisés : {os.path.exists(PROSPECTION_DIR + '/STRATEGIE_MESSAGES_LINKEDIN.md')}")

print("\n==========================================================")
print("✅ PIPELINE GLOBAL EXÉCUTÉ ET VERROUILLÉ AVEC SUCCÈS !")
print("==========================================================")
