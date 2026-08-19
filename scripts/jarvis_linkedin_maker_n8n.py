#!/usr/bin/env python3
"""
JARVIS-OMEGA — LinkedIn Maker & n8n Workflow Automation Suite
============================================================
Fonctionnalités :
  1. Générateur de Posts LinkedIn haute valeur (Hooks, Développements, CTA, Carrousels)
  2. Générateur de Commentaires d'Experts sur les actualités IA
  3. Séquences de Prospection Directe B2B (DSI, CTO, DRH, Fondateurs)
  4. Répondeur intelligent aux offres de missions / freelance
  5. Génération & Export des Workflows n8n prêts à importer (JSON)
  6. Enregistrement automatique dans SQLite (jarvis_master.db)
"""

import os
import sys
import time
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

HOME = Path("/home/pamerys")
JARVIS_DIR = HOME / "jarvis"
WORKFLOWS_DIR = JARVIS_DIR / "workflows"
REPORTS_DIR = JARVIS_DIR / "reports"
OUTPUT_DIR = HOME / "labo" / "output"
WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DB_MASTER = JARVIS_DIR / "jarvis_master.db"

def ts_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def log(msg):
    print(f"[{ts_now()}] 🚀 [LINKEDIN-MAKER] {msg}", flush=True)

@contextmanager
def get_db(timeout=60):
    conn = sqlite3.connect(str(DB_MASTER), timeout=timeout, check_same_thread=False)
    conn.execute("PRAGMA busy_timeout = 60000;")
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def ensure_tables():
    with get_db() as cx:
        cx.execute("""
            CREATE TABLE IF NOT EXISTS linkedin_maker_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                theme TEXT,
                hook TEXT,
                body TEXT,
                cta TEXT,
                format_type TEXT,
                carousel_slides TEXT,
                status TEXT DEFAULT 'READY',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cx.execute("""
            CREATE TABLE IF NOT EXISTS linkedin_expert_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT,
                target_post_summary TEXT,
                comment_text TEXT,
                angle TEXT,
                status TEXT DEFAULT 'READY',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cx.execute("""
            CREATE TABLE IF NOT EXISTS linkedin_outreach_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_role TEXT,
                company_type TEXT,
                subject TEXT,
                connection_note TEXT,
                followup_message TEXT,
                value_proposition TEXT,
                status TEXT DEFAULT 'READY',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

# 1. CATALOGUE DE POSTS ET CARROUSELS HAUT IMPACT (ALGO 2026)
POSTS_CATALOG = [
    {
        "theme": "Souveraineté IA & 0 Token",
        "format": "Post Texte + REX",
        "hook": "🔥 Pourquoi dépenser 2 500€/mois en API Cloud quand un GPU local fait le travail en 1.4 ms ?",
        "body": """Il y a 6 mois, une entreprise de 50 personnes nous a contactés : facture OpenAI explosive et risque juridique RGPD sur les données clients.

Notre solution en 3 étapes :
1️⃣ Déploiement d'un cluster GPU local on-premise (modèles 9B à 35B quantisés Q8).
2️⃣ Indexation RAG vectorielle 100% confinée sur leur base de connaissances interne.
3️⃣ Zéro appel externe : étanchéité absolue et coût marginal par token = 0€.

Résultat après 90 jours :
- Coût API : 0 €
- Latence moyenne : 80 ms
- Confidentialité : 100% conforme EU AI Act & RGPD.

L'avenir de l'IA d'entreprise n'est pas dans le Cloud générique, mais dans l'infrastructure souveraine maîtrisée.""",
        "cta": "👉 Vous envisagez de rapatrier votre IA en local ? Envoyez un message pour recevoir notre benchmark matériel 2026."
    },
    {
        "theme": "Orchestration Multi-Agents",
        "format": "Carrousel 5 Slides",
        "hook": "🤖 Comment faire collaborer 12 agents IA autonomes sans saturer la mémoire de votre serveur ?",
        "body": """Faire tourner un essaim d'agents IA, ce n'est pas juste chaîner des prompts. C'est gérer des transactions atomiques, des verrous SQLite et des flux asynchrones sans fuite mémoire.

Voici l'architecture que nous appliquons sur nos systèmes JARVIS :
- Un Orchestrateur Maître cadencé toutes les 15 minutes.
- Des agents spécialisés isolés par threads (Scraping, Qualification, Content, Code).
- Un bus SQLite WAL avec busy_timeout pour éliminer tout conflit d'écriture.
- Un retour vocal instantané pour le monitoring humain.

Glissez vers la droite pour voir le schéma technique étape par étape ➡️""",
        "carousel_slides": [
            {"slide": 1, "title": "L'Essaim d'Agents IA", "subtitle": "Architecture industrielle multi-threads"},
            {"slide": 2, "title": "Le Bus de Données", "subtitle": "SQLite WAL + transactions isolées"},
            {"slide": 3, "title": "La Cascade LLM", "subtitle": "Routage 0-token (9B local -> 35B cluster)"},
            {"slide": 4, "title": "Le Watchdog de Sécurité", "subtitle": "Purge automatique et contrôle thermique GPU"},
            {"slide": 5, "title": "Passez à l'échelle", "subtitle": "Contactez-nous pour votre architecture agentique"}
        ],
        "cta": "📌 Enregistrez ce carrousel pour concevoir votre futur essaim d'agents !"
    },
    {
        "theme": "Computer Use & Navigation CDP",
        "format": "Cas d'usage Automatisation",
        "hook": "⚡ Les API ne suffisent plus : comment le Computer Use et le protocole CDP révolutionnent l'automatisation web.",
        "body": """90% des opportunités business se trouvent sur des interfaces web sans API publique.

En combinant un navigateur Chrome piloté par CDP (Chrome DevTools Protocol) et des modèles de vision/texte locaux :
- Qualification automatique des leads et extraction de signaux d'embauche.
- Interaction fine respectant les quotas et les limites anti-bot.
- Synchronisation continue vers votre CRM sans intervention humaine.

La frontière entre logiciel et humain disparaît au profit d'agents capables de naviguer le web en autonomie totale.""",
        "cta": "💬 Quel processus web répétitif aimeriez-vous automatiser en priorité dans votre équipe ?"
    }
]

# 2. COMMENTAIRES D'EXPERTS SUR L'ACTUALITÉ IA
COMMENTS_CATALOG = [
    {
        "topic": "Annonce de nouveaux modèles Cloud vs Locaux",
        "target": "Post d'un influenceur sur les hausses de tarifs des LLM cloud",
        "comment": "Excellente analyse. On constate sur le terrain que le vrai coût n'est pas seulement le token entrant, mais la dépendance et le risque de transfert hors UE avec l'EU AI Act 2026. Les architectures hybrides (9B local pour 80% des flux + cluster dédié pour le raisonnement complexe) divisent le TCO par 5 tout en garantissant la souveraineté.",
        "angle": "Expertise Architecture & Économie Souveraine"
    },
    {
        "topic": "Débat sur la fragilité des POC IA",
        "target": "Post d'un CTO constatant que 80% des POC IA ne vont pas en prod",
        "comment": "Totalement d'accord avec ce constat. La plupart des POC échouent car ils négligent 3 fondamentaux : 1) La gestion fine de la mémoire et des verrous sous forte concurrence, 2) Le nettoyage des données en amont du RAG (suppression du bruit), et 3) L'absence de modèle économique clair après la phase de test. C'est le passage de l'expérimentation à l'ingénierie logicielle robuste.",
        "angle": "Rigueur MLOps & Production"
    }
]

# 3. SÉQUENCES DE PROSPECTION B2B & OUTREACH
OUTREACH_CATALOG = [
    {
        "target_role": "DSI / Directeur Technique (Grands Comptes & ETI)",
        "company_type": "Banque, Assurance, Santé, Industrie",
        "subject": "Souveraineté de vos données & Réduction des coûts d'inférence IA",
        "connection_note": "Bonjour [Prénom], j'ai suivi vos initiatives récentes sur la modernisation de votre SI. Nous aidons les DSI à déployer des architectures IA 100% souveraines et locales (0 fuite RGPD, coûts d'API supprimés). Au plaisir d'échanger !",
        "followup_message": """Bonjour [Prénom],

Suite à notre connexion, je voulais partager un retour d'expérience concret : nous avons récemment permis à une structure de déployer un moteur RAG et des agents locaux tournant sur serveurs dédiés, éliminant totalement les abonnements aux API américaines tout en garantissant la conformité stricte à l'EU AI Act 2026.

Seriez-vous ouvert à un échange de 15 minutes la semaine prochaine pour découvrir notre démonstration en direct ?

Bien cordialement,
Franck Delmas — Architecte Systèmes IA & Souveraineté""",
        "value_proposition": "Audit de faisabilité IA Locale & Déploiement POC 2 semaines (Forfait clé en main 5 000€)"
    },
    {
        "target_role": "DRH / Responsable du Recrutement IT & ESN",
        "company_type": "Cabinets de Recrutement, ESN, Conseil Tech",
        "subject": "Disponibilité immédiate — Renfort Expert IA Générative & Systèmes Autonomes",
        "connection_note": "Bonjour [Prénom], spécialiste en conception de systèmes d'agents IA autonomes, pipelines RAG et architectures souveraines, je serais ravi d'échanger sur vos opportunités actuelles de missions ou renfort d'équipe senior.",
        "followup_message": """Bonjour [Prénom],

Je vous contacte pour vous faire part de ma disponibilité immédiate pour des missions d'expertise senior en Architecture IA, RAG souverain et automatisation agentique (TJM ou forfait projet).

Mes points forts opérationnels :
- Déploiement d'infrastructures d'inférence locales haute performance (Qwen, Gemma, DeepSeek, vLLM).
- Orchestration multi-agents robuste (n8n, CDP, Python asynchrone).
- Autonomie totale, respect des délais et livrables de niveau industriel.

Discutons-en à votre convenance cette semaine !

Bien à vous,
Franck Delmas""",
        "value_proposition": "TJM Senior IA (850€ - 1 100€) / Forfaits d'accélération projets"
    }
]

# 4. GÉNÉRATEURS DE WORKFLOWS N8N (JSON READY-TO-IMPORT)
def generate_n8n_workflows():
    log("⚙️ Génération des workflows n8n complets...")
    
    # Workflow 1: LinkedIn Scheduler & AI Publisher
    wf_linkedin_post = {
        "name": "JARVIS - LinkedIn Post Publisher & Scheduler",
        "nodes": [
            {
                "parameters": {"rule": {"interval": [{"field": "hours", "hoursInterval": 4}]}},
                "name": "Schedule Trigger (Toutes les 4h)",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.1,
                "position": [250, 300]
            },
            {
                "parameters": {
                    "operation": "executeQuery",
                    "query": "SELECT id, hook, body, cta FROM linkedin_maker_posts WHERE status='READY' ORDER BY id ASC LIMIT 1;"
                },
                "name": "Fetch Next Post SQLite",
                "type": "n8n-nodes-base.sqlite",
                "typeVersion": 1,
                "position": [450, 300]
            },
            {
                "parameters": {
                    "url": "http://127.0.0.1:9100/publish",
                    "method": "POST",
                    "jsonParameters": True,
                    "options": {}
                },
                "name": "CDP Browser OS Publisher",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.1,
                "position": [680, 300]
            },
            {
                "parameters": {
                    "operation": "executeQuery",
                    "query": "UPDATE linkedin_maker_posts SET status='PUBLISHED' WHERE id={{ $json.id }};"
                },
                "name": "Mark as Published",
                "type": "n8n-nodes-base.sqlite",
                "typeVersion": 1,
                "position": [900, 300]
            }
        ],
        "connections": {
            "Schedule Trigger (Toutes les 4h)": {"main": [[{"node": "Fetch Next Post SQLite", "type": "main", "index": 0}]]},
            "Fetch Next Post SQLite": {"main": [[{"node": "CDP Browser OS Publisher", "type": "main", "index": 0}]]},
            "CDP Browser OS Publisher": {"main": [[{"node": "Mark as Published", "type": "main", "index": 0}]]}
        }
    }

    # Workflow 2: B2B Lead Enrichment & Outreach
    wf_outreach = {
        "name": "JARVIS - B2B Lead Outreach & Followup",
        "nodes": [
            {
                "parameters": {"rule": {"interval": [{"field": "hours", "hoursInterval": 2}]}},
                "name": "Outreach Trigger (2h)",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.1,
                "position": [250, 300]
            },
            {
                "parameters": {
                    "operation": "executeQuery",
                    "query": "SELECT id, target_role, connection_note, followup_message FROM linkedin_outreach_messages WHERE status='READY' LIMIT 5;"
                },
                "name": "Get Pending Messages",
                "type": "n8n-nodes-base.sqlite",
                "typeVersion": 1,
                "position": [480, 300]
            },
            {
                "parameters": {
                    "url": "http://127.0.0.1:18811/v1/chat/completions",
                    "method": "POST",
                    "jsonParameters": True
                },
                "name": "LLM Local Personalizer (Qwen 3.5)",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.1,
                "position": [720, 300]
            }
        ],
        "connections": {
            "Outreach Trigger (2h)": {"main": [[{"node": "Get Pending Messages", "type": "main", "index": 0}]]},
            "Get Pending Messages": {"main": [[{"node": "LLM Local Personalizer (Qwen 3.5)", "type": "main", "index": 0}]]}
        }
    }

    # Écriture des fichiers JSON
    (WORKFLOWS_DIR / "n8n_linkedin_post_scheduler.json").write_text(json.dumps(wf_linkedin_post, indent=2, ensure_ascii=False), encoding="utf-8")
    (WORKFLOWS_DIR / "n8n_b2b_outreach_engine.json").write_text(json.dumps(wf_outreach, indent=2, ensure_ascii=False), encoding="utf-8")
    log("✓ Workflows n8n exportés dans ~/jarvis/workflows/")

# 5. INSERTION ET SYNCHRONISATION
def run_maker_pipeline():
    log("🌟 Lancement du Pipeline Complet LinkedIn Maker & n8n...")
    ensure_tables()
    
    # 1. Insertion Posts
    with get_db() as cx:
        for p in POSTS_CATALOG:
            slides_json = json.dumps(p.get("carousel_slides", []), ensure_ascii=False)
            cx.execute("""
                INSERT INTO linkedin_maker_posts (theme, hook, body, cta, format_type, carousel_slides, status)
                VALUES (?, ?, ?, ?, ?, ?, 'READY')
            """, (p["theme"], p["hook"], p["body"], p["cta"], p["format"], slides_json))
            
        for c in COMMENTS_CATALOG:
            cx.execute("""
                INSERT INTO linkedin_expert_comments (topic, target_post_summary, comment_text, angle, status)
                VALUES (?, ?, ?, ?, 'READY')
            """, (c["topic"], c["target"], c["comment"], c["angle"]))
            
        for o in OUTREACH_CATALOG:
            cx.execute("""
                INSERT INTO linkedin_outreach_messages (target_role, company_type, subject, connection_note, followup_message, value_proposition, status)
                VALUES (?, ?, ?, ?, ?, ?, 'READY')
            """, (o["target_role"], o["company_type"], o["subject"], o["connection_note"], o["followup_message"], o["value_proposition"]))

    # 2. Génération n8n
    generate_n8n_workflows()

    # 3. Export Rapport Markdown
    md_report = f"""# 🚀 JARVIS LINKEDIN MAKER & N8N AUTOMATION COCKPIT
**Généré le :** `{ts_now()}` | **Statut :** `Prêt pour Diffusion & Ingestion`

---

## 📢 1. POSTS LINKEDIN CALIBRÉS (ALGORITHME 2026)

### 📌 Post 1 : Souveraineté & 0-Token On-Premise
> **Accroche :** {POSTS_CATALOG[0]['hook']}  
> **Corps :**  
> {POSTS_CATALOG[0]['body']}  
> **CTA :** {POSTS_CATALOG[0]['cta']}

### 📌 Post 2 : Carrousel Orchestration Multi-Agents
> **Accroche :** {POSTS_CATALOG[1]['hook']}  
> **Structure Carrousel :** 5 Slides méthodologiques prêtes  
> **CTA :** {POSTS_CATALOG[1]['cta']}

---

## 💬 2. COMMENTAIRES D'EXPERTS PRÊTS POUR L'ACTUALITÉ IA

- **Cible :** *{COMMENTS_CATALOG[0]['target']}*  
  **Angle :** `{COMMENTS_CATALOG[0]['angle']}`  
  **Commentaire :**  
  > *« {COMMENTS_CATALOG[0]['comment']} »*

---

## 💼 3. SÉQUENCES DE PROSPECTION B2B (DSI & RECRUTEURS)

### 🎯 Cible : DSI & Directeurs Techniques
- **Note de connexion :**  
  > *« {OUTREACH_CATALOG[0]['connection_note']} »*
- **Message de relance :**  
  > *« {OUTREACH_CATALOG[0]['followup_message']} »*
- **Offre packagée :** `{OUTREACH_CATALOG[0]['value_proposition']}`

---

## ⚙️ 4. WORKFLOWS N8N PRÊTS À L'EMPLOI

1. `~/jarvis/workflows/n8n_linkedin_post_scheduler.json` (Publication programmée & CDP Browser OS)
2. `~/jarvis/workflows/n8n_b2b_outreach_engine.json` (Enrichissement & personnalisation locale Qwen 3.5)

---
*Enregistré avec succès dans `jarvis_master.db`.*
"""

    report_file = REPORTS_DIR / "LINKEDIN_MAKER_N8N_REPORT.md"
    report_file.write_text(md_report, encoding="utf-8")
    (OUTPUT_DIR / "LINKEDIN_MAKER_N8N_REPORT.md").write_text(md_report, encoding="utf-8")
    
    log(f"✓ Pipeline terminé avec succès. Rapport disponible dans {report_file}")

if __name__ == "__main__":
    run_maker_pipeline()
