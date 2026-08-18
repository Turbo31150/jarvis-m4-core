#!/usr/bin/env python3
"""
prospection_recruteurs_toulouse.py — Générateur et gestionnaire de messages d'approche personnalisés
pour les recruteurs, ESN et décideurs Tech à Toulouse et Occitanie.
100% sans blabla, orienté ROI, architecture souveraine et cluster multi-GPU.
"""

import sqlite3
import os
import sys
from datetime import datetime

MASTER_DB = os.path.expanduser("~/jarvis/jarvis_master.db")
OUTPUT_DIR = os.path.expanduser("~/jarvis/data/prospection_toulouse_messages")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TEMPLATE_TECH_LEAD = """Bonjour {contact},

Je suis Franck Delmas, Ingénieur Systèmes & Architecte IA basé à Toulouse.

Je conçois et déploie des architectures d'IA souveraines et des swarms d'agents autonomes fonctionnant à 0 coût d'API récurrent (inférence locale sur clusters multi-GPU, bases SQLite FTS5/Postgres Swarm, protocoles délibératifs Table Ronde et transcription vocale temps réel WhisperFlow).

Mes réalisations récentes en production :
- JARVIS OS : Cluster distribué de 6 GPUs, système délibératif multi-experts et bibliothèque vivante (110 000+ blocs indexés).
- Pipeline Vocal Temps Réel (Lumen) : ASR local sous-titré et traduit sans latence ni dépendance cloud.
- Conformité Factur-X / B2B 2026 : Modules automatisés pour PME et plateformes SaaS.

Ayant une forte affinité avec les enjeux tech de {entreprise} sur le bassin toulousain ({secteur}), je serais ravi d'échanger 10 minutes avec vous sur vos besoins actuels (Architecte IA, Lead Dev Python/Rust, Déploiements On-Premise ou Conseil Stratégique).

Portfolio & Code : https://github.com/Turbo31150
Contact direct : franck@franckdelmas.dev / 06 19 82 27 06

Bien cordialement,
Franck Delmas
"""

def generate_messages():
    if not os.path.exists(MASTER_DB):
        print("Erreur: jarvis_master.db introuvable")
        return

    with sqlite3.connect(MASTER_DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM recruteurs_toulouse ORDER BY id").fetchall()

        print(f"\n{'='*75}")
        print(f"📍 PROSPECTION RECRUTEURS & ESN TOULOUSE — {len(rows)} CIBLES QUALIFIÉES")
        print(f"{'='*75}\n")

        for r in rows:
            msg = TEMPLATE_TECH_LEAD.format(
                contact=r["contact"] or "l'équipe Recrutement",
                entreprise=r["entreprise"],
                secteur=r["secteur"]
            )
            # Sauvegarder dans un fichier markdown individuel
            slug = r["entreprise"].lower().replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '')
            file_path = os.path.join(OUTPUT_DIR, f"{r['id']:02d}_{slug}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"DESTINATAIRE : {r['entreprise']} <{r['email']}>\n")
                f.write(f"OBJET : Profil Ingénieur IA Souveraine & Architecte Systèmes — Franck Delmas (Toulouse)\n")
                f.write(f"{'-'*60}\n\n")
                f.write(msg)

            print(f"  ✉️ [{r['id']:02d}] {r['entreprise']:<38} | {r['email']:<35} -> {os.path.basename(file_path)}")

    print(f"\n✅ Tous les messages personnalisés sont générés dans : {OUTPUT_DIR}\n")

if __name__ == "__main__":
    generate_messages()
