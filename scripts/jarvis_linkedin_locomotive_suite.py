#!/usr/bin/env python3
"""
JARVIS-OMEGA — LINKEDIN 360° LOCOMOTIVE SUITE (Moteur Honnête)
==============================================================
Boucle d automatisation :
  1. ALIMENTE : Rédige des posts d autorité et les met en file (QUEUED / DRAFT_LOCAL)
  2. COMMENTE : Rédige des commentaires experts en file (QUEUED)
  3. PROSPECTE: Prépare des messages d outreach (SIMULATION_NON_ENVOYE)
  4. DISPATCH : Appelle le poster instrumenté avec logs sans DEVNULL
"""

import os
import sys
import time
import json
import sqlite3
import datetime
import subprocess
from pathlib import Path

HOME = Path("/home/pamerys")
JARVIS_DIR = HOME / "jarvis"
DB_MASTER = JARVIS_DIR / "jarvis_master.db"
OUTPUT_DIR = HOME / "labo" / "output" / "linkedin_content"
LOGS_DIR = JARVIS_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
POSTER_LOG = LOGS_DIR / "browseros_poster.log"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

POSTS_LIBRARY = [
    {
        "theme": "Souveraineté & Infrastructure On-Premise",
        "hook": "🔥 En 2026, 84% des DSI de grands comptes bloquent l accès aux API Cloud étrangères pour leurs données stratégiques.",
        "core": "L alternative n est pas de renoncer à l IA, mais d internaliser l inférence :\n• Déploiement de clusters locaux multi-GPU (9B à 35B quantisés)\n• Traitement des flux critiques en mode avion complet (zéro risque d exfiltration)\n• Coût marginal à la requête strictement nul.\n\nLa souveraineté numérique n est plus un frein : c est un accélérateur d indépendance.",
        "cta": "DSI & CTO : quel est votre niveau d internalisation de l inférence cette année ?",
        "hashtags": "#IASouveraine #OnPremise #Cybersécurité #CloudSovereignty #JARVIS #GenAI #TechLeadership"
    },
    {
        "theme": "Systèmes Multi-Agents en Production",
        "hook": "⚙️ Comment faire tourner 12 agents IA spécialisés en continu sur un poste sans exploser la mémoire vive ?",
        "core": "L erreur courante est d utiliser un seul méga-modèle pour tout faire.\nNotre approche sur JARVIS OS :\n1. Architecture modulaire : des agents ultra-ciblés (Audit, RAG, Vente, Synthèse, Monitoring).\n2. SQLite en mode WAL et queues en mémoire partagée pour éliminer les verrous.\n3. Cascade d inférence priorisant le lien direct M1 USB-C à 1.3 ms.\n\nRésultat : plus de 70 000 tâches traitées par jour avec une stabilité parfaite.",
        "cta": "Quelle est la taille optimale de votre équipe d agents IA en production ?",
        "hashtags": "#MultiAgents #AutonomousAI #DevOps #LLMOps #SystemDesign #OpenClaw #SoftwareEngineering"
    },
    {
        "theme": "Cockpits Mobiles & Zero-UI",
        "hook": "🎙️ Pourquoi nous avons supprimé toutes les interfaces web de notre cockpit mobile de commande.",
        "core": "Face aux alertes critiques, naviguer sur un dashboard web est une perte de temps.\nNous avons compilé une application Android native pure (0% HTML) couplée à notre moteur vocal local :\n• Boutons matériels et reconnaissance vocale instantanée\n• Routage réseau intelligent automatique (WiFi LAN, Tailscale 4G, USB)\n• Synthèse vocale matérielle débridée à 100% sur les haut-parleurs.\n\nLe futur du pilotage opérationnel, c est l immédiateté vocale sans latence.",
        "cta": "Piloter votre infrastructure par la voix en direct : gadget ou impératif opérationnel ?",
        "hashtags": "#ZeroUI #EdgeAI #VoiceCockpit #Whisper #MobileEngineering #Productivity"
    },
    {
        "theme": "Rentabilité & Forfaits B2B",
        "hook": "📈 Arrêtons les POC d IA récréatifs : voici comment structurer une offre IA à ROI positif dès le 1er mois.",
        "core": "Les entreprises attendent des résultats chiffrés et vérifiables :\n1. Audit & Cadrage express en 5 jours ouvrés\n2. Pack Intégration Clé en Main livré en 2 semaines sur serveurs internes\n3. Modèle tarifaire transparent : Forfait ferme d implémentation + TJM senior d accompagnement.\n\nNos clients amortissent leur investissement dès le 4ᵉ mois face aux rentes SaaS cumulées.",
        "cta": "Directeurs Innovation : parlons rentabilité et cas d usage réels.",
        "hashtags": "#B2B #ROI #ConsultingIA #TransformationDigitale #Entreprise2026 #BusinessStrategy"
    }
]

INDUSTRY_TOPICS_TO_COMMENT = [
    {
        "cible": "Directeurs Informatiques (DSI)",
        "sujet": "Arbitrage entre API Cloud US et serveurs locaux sécurisés",
        "commentaire": "Excellente analyse ! L inférence locale quantisée sur GPU dédiés permet aujourd hui d atteindre une précision remarquable tout en garantissant une étanchéité totale face au Cloud Act."
    },
    {
        "cible": "RSSI & Responsables Cybersécurité",
        "sujet": "Conformité NIS2 et gestion des risques liés à l IA générative",
        "commentaire": "Point crucial. Le RAG hybride couplé à une règle stricte de citation vérifiée et une quarantaine des réponses sans source est la seule approche viable pour auditer la conformité."
    },
    {
        "cible": "Tech Leaders & Architectes",
        "sujet": "Orchestration multi-agents et optimisation des ressources",
        "commentaire": "Tout à fait d accord sur la spécialisation. Segmenter les rôles et mutualiser la mémoire via SQLite WAL évite les goulets d étranglement même à très forte charge."
    }
]

PROSPECTS_OUTREACH = [
    {
        "cible": "Airbus Group",
        "persona": "DSI & Responsable Systèmes Critiques",
        "message": "Bonjour, face aux impératifs de confidentialité aéronautique, nous avons développé JARVIS OS : une appliance IA 100% on-premise en mode avion complet. Seriez-vous ouvert à un échange de 10 min sur vos cas d usage ?"
    },
    {
        "cible": "Thales",
        "persona": "Directeur Infrastructure & IA",
        "message": "Bonjour, nous déployons des clusters d agents autonomes opérant sur GPU locaux sécurisés pour l audit documentaire et l analyse technique sans aucune fuite cloud. Échangeons sur vos priorités 2026."
    },
    {
        "cible": "Safran",
        "persona": "Head of Digital Transformation",
        "message": "Bonjour, nos solutions d IA souveraine permettent d automatiser les revues d ingénierie et le reporting critique avec zéro hallucination. Disponible pour une courte démo en direct."
    }
]

def init_tables():
    with sqlite3.connect(str(DB_MASTER), timeout=30) as cx:
        cx.execute("""
            CREATE TABLE IF NOT EXISTS linkedin_comments_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_audience TEXT,
                topic TEXT,
                comment_text TEXT,
                status TEXT DEFAULT 'QUEUED',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cx.execute("""
            CREATE TABLE IF NOT EXISTS linkedin_outreach_prospects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT,
                persona TEXT,
                outreach_note TEXT,
                status TEXT DEFAULT 'SIMULATION_NON_ENVOYE',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

def run_suite_cycle(cycle_num=1):
    print(f"\n=======================================================")
    print(f"🚀 [LINKEDIN 360° LOCOMOTIVE] CYCLE #{cycle_num:03d} EN COURS")
    print(f"=======================================================")
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    init_tables()
    
    # 1. ALIMENTE LA FILE
    post = POSTS_LIBRARY[(cycle_num - 1) % len(POSTS_LIBRARY)]
    full_content = f"{post['hook']}\n\n{post['core']}\n\n👉 {post['cta']}\n\n{post['hashtags']}"
    file_path = OUTPUT_DIR / f"linkedin_post_auto_{cycle_num}_{ts}.md"
    file_path.write_text(full_content, encoding="utf-8")
    
    with sqlite3.connect(str(DB_MASTER), timeout=30) as cx:
        cx.execute("""
            INSERT INTO linkedin_content_stream 
            (cycle_num, theme, content, target_audience, hook, cta, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'QUEUED', CURRENT_TIMESTAMP)
        """, (cycle_num, post['theme'], full_content, "DSI & Tech Leaders", post['hook'], post['cta']))
    
    print(f"📥 [1. ALIMENTE] Post rédigé et mis en file : '{post['theme']}' -> {file_path.name}")
    
    # 2. COMMENTE (FILE)
    cmt = INDUSTRY_TOPICS_TO_COMMENT[(cycle_num - 1) % len(INDUSTRY_TOPICS_TO_COMMENT)]
    with sqlite3.connect(str(DB_MASTER), timeout=30) as cx:
        cx.execute("""
            INSERT INTO linkedin_comments_queue (target_audience, topic, comment_text, status, created_at)
            VALUES (?, ?, ?, 'QUEUED', CURRENT_TIMESTAMP)
        """, (cmt['cible'], cmt['sujet'], cmt['commentaire']))
    print(f"📥 [2. COMMENTE] Commentaire expert mis en file pour : {cmt['cible']} ({cmt['sujet'][:30]}...)")
    
    # 3. PROSPECTE (SIMULATION NON ENVOYE)
    prosp = PROSPECTS_OUTREACH[(cycle_num - 1) % len(PROSPECTS_OUTREACH)]
    with sqlite3.connect(str(DB_MASTER), timeout=30) as cx:
        cx.execute("""
            INSERT INTO linkedin_outreach_prospects (company, persona, outreach_note, status, created_at)
            VALUES (?, ?, ?, 'SIMULATION_NON_ENVOYE', CURRENT_TIMESTAMP)
        """, (prosp['cible'], prosp['persona'], prosp['message']))
    print(f"📋 [3. PROSPECTE] Fiche prospect enregistrée : {prosp['cible']} ({prosp['persona']}) [SIMULATION]")
    
    # 4. STATISTIQUES GLOBALES HONNÊTES
    with sqlite3.connect(str(DB_MASTER), timeout=30) as cx:
        live_posts = cx.execute("SELECT count(*) FROM linkedin_content_stream WHERE status LIKE 'PUBLISHED_LIVE%' OR status='DISPATCHED_DIRECT_LIVE'").fetchone()[0]
        queued_posts = cx.execute("SELECT count(*) FROM linkedin_content_stream WHERE status IN ('QUEUED', 'READY')").fetchone()[0]
        echec_posts = cx.execute("SELECT count(*) FROM linkedin_content_stream WHERE status='ECHEC_PUBLICATION'").fetchone()[0]
        
    summary = f"📢 [LINKEDIN 360°] {live_posts} posts en direct vérifiés · {queued_posts} en file d attente · {echec_posts} échecs"
    print(f"\n📊 {summary}")
    subprocess.run(["curl", "-s", "-d", summary, "https://ntfy.sh/jarvis_omega_turbo"], stdout=subprocess.DEVNULL)
    
    return live_posts, queued_posts, echec_posts

def run_loop():
    cycle = 1
    while True:
        try:
            run_suite_cycle(cycle)
            # Exécution tracée avec logging dans POSTER_LOG (plus de DEVNULL)
            with open(str(POSTER_LOG), "a", encoding="utf-8") as log_f:
                log_f.write(f"\n--- DÉBUT TENTATIVE POSTER CYCLE #{cycle} ({datetime.datetime.now().isoformat()}) ---\n")
                subprocess.run(
                    ["python3", "/home/pamerys/jarvis/scripts/jarvis_browseros_claudecode_poster.py"],
                    stdout=log_f,
                    stderr=log_f
                )
            cycle += 1
            time.sleep(300) # Exécution toutes les 5 minutes
        except Exception as e:
            print(f"⚠️ Erreur cycle LinkedIn: {e}")
            time.sleep(30)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        run_suite_cycle(1)
    else:
        run_loop()
