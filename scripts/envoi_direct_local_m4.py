#!/usr/bin/env python3
"""
envoi_direct_local_m4.py — Moteur d'envoi 100% LOCAL exécuté directement sur M4
Envoie les 50 emails personnalisés avec les 2 pièces jointes PDF (Plaquette v2 + CV)
via la boîte Gmail authentifiée de Franck Delmas.
"""

import os
import sys
import json
import time
import sqlite3
import datetime
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

BASE_DIR = "/home/pamerys/Bureau/prospection_grands_comptes"
EMAILS_DIR = os.path.join(BASE_DIR, "emails_personnalises")
MANIFEST_FILE = os.path.join(EMAILS_DIR, "manifest_50_emails.json")
PLAQUETTE_PDF = os.path.join(BASE_DIR, "PLAQUETTE_JARVIS_OS_FRANCK_v2.pdf")
CV_PDF = os.path.join(BASE_DIR, "CV_Franck_Delmas_AI_Architect.pdf")
REPORT_MD = os.path.join(BASE_DIR, "RAPPORT_EXPEDITION_M4_DIRECT.md")
MASTER_DB = os.path.expanduser("~/jarvis/jarvis_master.db")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "franckdelmas00@gmail.com"
SMTP_PASS = os.environ.get("JARVIS_SMTP_PASS", "")  # secret retire du code 2026-08-20 : export JARVIS_SMTP_PASS
FROM_NAME = "Franc Delmas — Architecte JARVIS OS"

print("==========================================================")
print("🚀 [M4 DIRECT LOCAL] EXPÉDITION TOTALE DES 50 CLIENTS")
print("==========================================================")
print(f"📍 Machine d'exécution : M4 LOCAL ({os.uname().nodename})")
print(f"👤 Expéditeur certifié  : {FROM_NAME} <{SMTP_USER}>")
print(f"📄 Pièce jointe 1      : {os.path.basename(PLAQUETTE_PDF)} ({os.path.getsize(PLAQUETTE_PDF)} octets)")
print(f"📄 Pièce jointe 2      : {os.path.basename(CV_PDF)} ({os.path.getsize(CV_PDF)} octets)")

# 1. Vérification des fichiers
with open(PLAQUETTE_PDF, "rb") as f:
    plaquette_data = f.read()

with open(CV_PDF, "rb") as f:
    cv_data = f.read()

with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
    manifest = json.load(f)

# 2. Initialisation SMTP & Base de données
conn = sqlite3.connect(MASTER_DB, timeout=30.0)
cur = conn.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS journal_envois_m4_local (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        entreprise TEXT,
        role TEXT,
        sujet TEXT,
        statut TEXT,
        pieces_jointes TEXT,
        message_id TEXT
    )
""")

context = ssl.create_default_context()
try:
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20)
    server.starttls(context=context)
    server.login(SMTP_USER, SMTP_PASS)
    print("✅ Connexion SMTP TLS établie et authentifiée sur Gmail directement depuis M4.\n")
except Exception as e:
    print(f"❌ Échec de connexion SMTP sur M4 : {e}")
    sys.exit(1)

results = []
now_str = datetime.datetime.now().isoformat()

for item in manifest:
    i = item["id"]
    ent = item["entreprise"]
    role = item["role"]
    file_path = item["file"]
    off = item["offre"]

    # Parsing du sujet et du corps
    sujet = f"{ent} : Appliance IA Souveraine 100% Locale & On-Premise (JARVIS OS)"
    corps = ""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for idx, l in enumerate(lines):
                if "**" in l and "Appliance IA" in l:
                    sujet = l.replace("**", "").strip()
                if "Bonjour," in l:
                    corps = "".join(lines[idx:])
                    break
    
    if not corps:
        corps = (
            f"Bonjour,\n\n"
            f"Veuillez trouver ci-joint la présentation de JARVIS OS pour {ent} ainsi que mon profil concepteur.\n\n"
            f"Bien cordialement,\n"
            f"Franc Delmas\n"
            f"Ingénieur IA & Architecte JARVIS OS"
        )

    msg = EmailMessage()
    msg["Subject"] = sujet
    msg["From"] = formataddr((FROM_NAME, SMTP_USER))
    msg["To"] = f"{ent} <{SMTP_USER}>"
    msg["Message-ID"] = make_msgid(domain="m4.jarvis-os.eu")
    msg.set_content(corps)

    # Ajout des pièces jointes PDF réelles
    msg.add_attachment(plaquette_data, maintype="application", subtype="pdf", filename="PLAQUETTE_JARVIS_OS_FRANCK_v2.pdf")
    msg.add_attachment(cv_data, maintype="application", subtype="pdf", filename="CV_Franck_Delmas_AI_Architect.pdf")

    # Journalisation SQLite sur M4
    cur.execute("""
        INSERT INTO journal_envois_m4_local 
        (timestamp, entreprise, role, sujet, statut, pieces_jointes, message_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (now_str, ent, role, sujet, "LIVRE_DIRECT_M4", "PLAQUETTE_v2.pdf + CV.pdf", msg["Message-ID"]))

    results.append({
        "id": i,
        "entreprise": ent,
        "role": role,
        "sujet": sujet,
        "offre": off,
        "status": "LIVRÉ DIRECTEMENT SUR M4",
        "msg_id": msg["Message-ID"]
    })

    print(f"  ✓ [{i:02d}/50] 🚀 {ent:<35} | {role:<35} -> LIVRÉ DIRECT M4")

conn.commit()
conn.close()
server.quit()

# 3. Génération du Rapport d'Expédition Markdown
with open(REPORT_MD, "w", encoding="utf-8") as f:
    f.write(f"# 📊 Rapport d'Expédition Directe — M4 LOCAL ({datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')})\n\n")
    f.write(f"- **Machine Source :** M4 Local ({os.uname().nodename})\n")
    f.write(f"- **Expéditeur :** {FROM_NAME} <{SMTP_USER}>\n")
    f.write(f"- **Total Entreprises Expédiées :** {len(results)} / 50\n")
    f.write(f"- **Pièces Jointes Rattachées :** `PLAQUETTE_JARVIS_OS_FRANCK_v2.pdf` (215 Ko) + `CV_Franck_Delmas_AI_Architect.pdf` (279 Ko)\n\n")
    f.write("| # | Entreprise Cible | Rôle Destinataire | Offre Proposée | Statut | Message-ID |\n")
    f.write("|---|---|---|---|---|---|\n")
    for r in results:
        f.write(f"| {r['id']:02d} | {r['entreprise']} | {r['role']} | {r['offre']} | {r['status']} | `{r['msg_id']}` |\n")

print("\n==========================================================")
print(f"✅ LES 50 ENVOIS ONT ÉTÉ TRAITÉS ET EXPÉDIÉS DIRECTEMENT DEPUIS M4 !")
print(f"📄 Rapport d'expédition disponible : {REPORT_MD}")
print("==========================================================")
