#!/usr/bin/env python3
"""
JARVIS-OMEGA — Massive Swarm Todo List & Role-Based Capability Dispatcher
========================================================================
"""

import os
import sys
import json
import time
import sqlite3
import datetime
import subprocess
from pathlib import Path

DB_MASTER = Path("/home/pamerys/jarvis/jarvis_master.db")
REPORTS_DIR = Path("/home/pamerys/jarvis/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
SWARM_REPORT = REPORTS_DIR / "SWARM_12_AGENTS_MASSIVE_TODOLIST.md"

SWARM_ROSTER = [
    {
        "id": 1,
        "name": "Agent-01: Architecte Système Souverain",
        "model": "M1 (qwen3.5-35b / 10.42.0.230)",
        "role": "Conception d'architectures On-Premise, conformité NIS2 et gouvernance EU AI Act",
        "capabilities": ["Audit d'infrastructure", "Sécurité matérielle", "Diagrammes d'architecture C4"],
        "todo_tasks": [
            "Finaliser le dossier de cadrage d'étanchéité NIS2 pour Airbus Commercial & Space",
            "Modéliser la topologie multi-GPU On-Premise pour Thales Alenia Space",
            "Rédiger la charte de souveraineté des données médicales HDS pour Sanofi",
            "Établir les matrices de cyber-résilience pour Dassault Aviation"
        ]
    },
    {
        "id": 2,
        "name": "Agent-02: Lead Inférence Locale & Multi-GPU",
        "model": "M1 (6 GPUs ASIX Gigabit)",
        "role": "Optimisation des temps d'inférence, quantisation GGUF/EXL2 et parallélisme",
        "capabilities": ["Quantisation Q4_K_M/Q8_0", "vLLM / LMStudio tuning", "Latence < 15ms"],
        "todo_tasks": [
            "Optimiser le débit token/s sur Qwen 3.5 27B pour les requêtes parallèles",
            "Créer les profils de mémoire VRAM pour modèles 9B à 35B sans débordement",
            "Auditer le lien direct USB-C ASIX 10.42.0.230 sous charge 100 concurrents",
            "Bancariser les scripts d'auto-fallback M1 -> M2 -> OL1"
        ]
    },
    {
        "id": 3,
        "name": "Agent-03: Moteur RAG Hybride 768d & BM25",
        "model": "OL1 (nomic-embed-text / 768d)",
        "role": "Indexation vectorielle dense, reranking RRF et citations vérifiées [n]",
        "capabilities": ["Recherche sémantique", "Fusion Reciprocal Rank Fusion", "0 hallucination"],
        "todo_tasks": [
            "Maintenir l'indexation permanente dense 768d sur jarvis_vector_store.db",
            "Injecter les manuels techniques et normes NIS2 dans la base de vecteurs",
            "Calibrer le score RRF pour prioriser les documents certifiés",
            "Valider l'extraction de citations exactes avec numérotation de paragraphe"
        ]
    },
    {
        "id": 4,
        "name": "Agent-04: Développeur Multi-Agents SQLite WAL",
        "model": "M2 (deepseek-r1 / 192.168.1.26)",
        "role": "Orchestration asynchrone, locks SQLite sans contention et tables maîtres",
        "capabilities": ["Python AsyncIO", "SQLite WAL tuning", "Bus d'événements IPC"],
        "todo_tasks": [
            "Optimiser les transactions SQLite à > 10 000 écritures/seconde sans blocage",
            "Déployer les triggers automatiques sur la table generated_business_tasks",
            "Garantir la cohérence des checkpoints WAL lors des salves 10k",
            "Nettoyer les verrous zombies lors des redémarrages de containers"
        ]
    },
    {
        "id": 5,
        "name": "Agent-05: Expert Automatisation n8n & OpenClaw",
        "model": "Conteneur Local (jarvis-n8n:5678)",
        "role": "Workflows No-Code/Low-Code, webhooks et automatisation de processus métiers",
        "capabilities": ["Workflows n8n", "OpenClaw Engine", "Connecteurs REST/GraphQL"],
        "todo_tasks": [
            "Automatiser le flux de réception de leads et génération instantanée de devis",
            "Synchroniser les statuts des 50 comptes cibles OpenClaw",
            "Tester les nœuds de déclenchement webhook pour les alertes critiques",
            "Créer les connecteurs de sauvegarde automatique vers /storage/"
        ]
    },
    {
        "id": 6,
        "name": "Agent-06: Ingénieur SOC & Forensique LLM",
        "model": "M1 (qwen2.5-coder-14b)",
        "role": "Surveillance SIEM, détection d'intrusions et analyse de logs temps réel",
        "capabilities": ["Audit de sécurité", "Détection d'injection de prompt", "Parsing syslog"],
        "todo_tasks": [
            "Analyser les logs de connexion pour détecter toute tentative de scan",
            "Valider l'étanchéité totale du réseau Tailscale (6 nœuds sécurisés)",
            "Déployer les filtres d'assainissement sur toutes les entrées de formulaires",
            "Établir le rapport hebdomadaire d'intégrité des clés et credentials"
        ]
    },
    {
        "id": 7,
        "name": "Agent-07: Architecte Zero-UI & Voix Neuronale",
        "model": "Local (Edge-TTS / ALSA / S8 S9)",
        "role": "Synthèse vocale ultra-rapide, commandes vocales et interactions mains-libres",
        "capabilities": ["Edge-TTS Remy", "ALSA plughw:1,0", "ADB bridge Samsung S8/S9"],
        "todo_tasks": [
            "Maintenir la latence de synthèse vocale sous les 200 ms",
            "Surveiller le canal vocal S8/S9 sur le port 8799 via reverse forward",
            "Générer les briefings audio automatiques à chaque fin de cycle 5 min",
            "Gérer les interruptions vocales lors des commandes prioritaires"
        ]
    },
    {
        "id": 8,
        "name": "Agent-08: Analyste FinOps & ROI Souverain",
        "model": "M1 (glm-4.7-flash)",
        "role": "Calcul des économies de coûts, modélisation financière et TCO On-Premise vs Cloud",
        "capabilities": ["Calcul de ROI", "Matrices TCO sur 3 ans", "Chiffrage devis PME/ETI"],
        "todo_tasks": [
            "Calculer l'économie générée par 210 000 requêtes traitées 0€ de token",
            "Modéliser le seuil de rentabilité matériel pour serveurs GPU 4x RTX",
            "Mettre à jour les grilles tarifaires de forfaits d'intégration (55k€ - 190k€)",
            "Intégrer les comparatifs de coûts dans les propositions commerciales"
        ]
    },
    {
        "id": 9,
        "name": "Agent-09: Directeur Commercial B2B & Grands Comptes",
        "model": "M1 (qwen3.5-35b)",
        "role": "Prospection ciblée CAC40/ETI, rédaction d'offres et négociation de forfaits",
        "capabilities": ["Pitches d'ingénierie", "Propositions PDF chiffrées", "Outreach DSI"],
        "todo_tasks": [
            "Piloter l'envoi des devis personnalisés aux 10 grands comptes prioritaires",
            "Assurer le suivi des candidatures de Franck Delmas (TJM 950€ - 1 200€)",
            "Formuler les relances commerciales à J+2 pour les décideurs contactés",
            "Tenir à jour le pipeline de chiffre d'affaires prévisionnel en base SQLite"
        ]
    },
    {
        "id": 10,
        "name": "Agent-10: Scraper d'Actualité & Rédacteur d'Autorité",
        "model": "OL1 (qwen2.5:7b)",
        "role": "Veille stratégique, analyse des tendances et rédaction de commentaires percutants",
        "capabilities": ["Scraping flux RSS & Web", "Formulation d'accroches virales", "SEO & Copywriting"],
        "todo_tasks": [
            "Moissonner les actualités chaudes sur NIS2, RGPD, santé et défense",
            "Générer des commentaires de haute autorité pour chaque fil tendance",
            "Optimiser les formats carrousels et textes pour maximiser la visibilité",
            "Alimenter la table linkedin_comments_queue à chaque salve 5 min"
        ]
    },
    {
        "id": 11,
        "name": "Agent-11: Sniffer de Missions & Recrutement IA",
        "model": "OL1 (gemma3:4b)",
        "role": "Détection d'opportunités freelance, qualification de leads et positionnement rapide",
        "capabilities": ["Parsing offres d'emploi", "Matching compétences", "Préparation candidatures"],
        "todo_tasks": [
            "Capter les offres de Lead AI Engineer et Architecte IA sous 48h",
            "Positionner immédiatement le profil de Franck Delmas sur les missions à fort TJM",
            "Attacher la plaquette et le CV aux dossiers de candidature",
            "Enregistrer les opportunités qualifiées dans moisson_missions_linkedin"
        ]
    },
    {
        "id": 12,
        "name": "Agent-12: Auditeur Qualité, CI/CD & Auto-Amélioration",
        "model": "M1 / Gemini Flash",
        "role": "Supervision des processus, vérification de l'état des services et zéro déchet",
        "capabilities": ["Health checks", "Auto-debug de code", "Purge disque automatique"],
        "todo_tasks": [
            "Vérifier la santé des 10 terminaux tmux de la session jarvis",
            "Appliquer la règle stricte du Zéro Déchet (/tmp/ purgé en continu)",
            "Garantir le bon fonctionnement de la liaison M1 Gigabit 10.42.0.230",
            "Générer le rapport consolidé de performance pour l'ingénieur"
        ]
    }
]

def dispatch_swarm_todolist():
    print("==================================================================")
    print("🚀 [SWARM TODOLIST DISPATCHER] DÉPLOIEMENT DES MISSIONS DES 12 AGENTS")
    print("==================================================================")

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with sqlite3.connect(str(DB_MASTER), timeout=30) as cx:
        for agent in SWARM_ROSTER:
            tasks_desc = f"Rôle: {agent['role']} | Modèle: {agent['model']}"
            output_summ = f"4 Tâches Assignées: " + " · ".join(agent["todo_tasks"][:2])
            
            cx.execute("""
                INSERT INTO swarm_agent_executions 
                (agent_id, agent_name, task_description, output_summary, status, created_at)
                VALUES (?, ?, ?, ?, 'DISPATCHED_ACTIVE', CURRENT_TIMESTAMP)
            """, (agent["id"], agent["name"], tasks_desc, output_summ))

            for task in agent["todo_tasks"]:
                cx.execute("""
                    INSERT INTO generated_business_tasks 
                    (cycle_num, category, title, payload, status, priority, created_at)
                    VALUES (2026, ?, ?, ?, 'IN_PROGRESS', 1, CURRENT_TIMESTAMP)
                """, (f"SWARM_{agent['name'].split(':')[0].upper()}", task, json.dumps({"agent": agent["name"], "model": agent["model"]}, ensure_ascii=False)))

            print(f"  ✓ [{agent['id']:02d}/12] 🤖 {agent['name']:<42} -> {len(agent['todo_tasks'])} Tâches assignées ({agent['model']})")

    # Génération du Rapport Markdown Consolidé
    md_content = f"""# 🤖 JARVIS OS — TODOLIST MASSIVE & AFFECTATION DES 12 AGENTS DE L'ESSAIM
*Généré le {now_str} par JARVIS-OMEGA (Mode 100% Autonome)*

---

## 🏛️ 1. CARTOGRAPHIE DES MODÈLES & CAPACITÉS DU CLUSTER

| Agent | Rôle & Spécialité | Modèle Assigné | Capacités Clés |
|---|---|---|---|
"""
    for a in SWARM_ROSTER:
        caps = ", ".join(a["capabilities"])
        md_content += f"| **{a['name']}** | {a['role']} | `{a['model']}` | {caps} |\n"

    md_content += "\n---\n\n## 📋 2. FEUILLE DE ROUTE DÉTAILLÉE PAR AGENT\n\n"

    for a in SWARM_ROSTER:
        md_content += f"### 🚀 {a['name']}\n"
        md_content += f"- **Modèle & Infrastructure :** `{a['model']}`\n"
        md_content += f"- **Mission Principale :** *{a['role']}*\n"
        md_content += "- **Tâches Immédiates Assignées :**\n"
        for t in a["todo_tasks"]:
            md_content += f"  - [ ] ⚡ {t}\n"
        md_content += "\n"

    md_content += """---
## ⚡ 3. RÈGLES D'ORCHESTRATION & EXÉCUTION
- **Zéro Rétention :** Tout livrable complété est instantanément transmis sur son canal de diffusion.
- **Mémoire Commune :** Synchronisation bidirectionnelle via `jarvis_master.db` (mode SQLite WAL).
- **Zéro Déchet :** Purge continue de `/tmp/` après chaque cycle.
"""

    with open(str(SWARM_REPORT), "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"\n✓ Rapport d'affectation Swarm généré : {SWARM_REPORT}")

    # Nettoyage Zéro-Déchet
    os.system("rm -f /tmp/*.png /tmp/*.xml /tmp/*.3gp /tmp/*.wav /tmp/*.mp3 2>/dev/null")
    print("🧹 Nettoyage Zéro-Déchet effectué.")

    summary = f"🎉 [TODOLIST SWARM DÉPLOYÉE] 48 Tâches majeures réparties sur les 12 Agents selon leurs capacités et modèles !"
    print(f"\n{summary}")
    subprocess.run(["curl", "-s", "-d", summary, "https://ntfy.sh/jarvis_omega_turbo"], stdout=subprocess.DEVNULL)

    try:
        subprocess.run(['edge-tts', '--voice', 'fr-FR-RemyMultilingualNeural', '--text', 'Todolist massive et affectation des douze agents déployées avec succès.', '--write-media', '/tmp/swarm_todo.mp3'], timeout=10)
        subprocess.run(['ffmpeg', '-y', '-i', '/tmp/swarm_todo.mp3', '-filter:a', 'volume=6.0', '-ar', '48000', '-ac', '2', '/tmp/swarm_todo.wav'], timeout=10)
        subprocess.Popen(['aplay', '-D', 'plughw:1,0', '/tmp/swarm_todo.wav'])
    except Exception:
        pass

if __name__ == "__main__":
    dispatch_swarm_todolist()
