#!/usr/bin/env python3
"""
JARVIS — Phase 4 : Enregistrement hiérarchie agents (nom, mission, prompt, tier, clé SSH, TOTP)
Structure : Tier1=Orchestrateurs | Tier2=Spécialistes | Tier3=Workers
Exécuter : python3 /home/pamerys/jarvis/infra/scripts/04_register_agents_hierarchy.py
"""

import sqlite3
import os
import subprocess
from datetime import datetime

DB = "/home/pamerys/jarvis/data/jarvis.db"
SSH_DIR = "/home/pamerys/jarvis/backups/ssh-access"

# Définition hiérarchique — compléter missions/prompts selon besoins
AGENTS = [
    # Tier 1 — Orchestrateurs
    {
        "id": "jarvis-master",
        "name": "JARVIS Master",
        "mission": "Orchestrateur central. Coordonne tous les agents, reçoit les ordres top-level, dispatche.",
        "system_prompt": "Tu es JARVIS Master. Tu orchestes les agents spécialisés. Tu ne fais jamais de tâches directement sauf décision architecturale critique.",
        "node": "M1",
        "tier": 1,
        "container_name": "jarvis-master",
    },
    {
        "id": "jarvis-prompt-dispatcher",
        "name": "Prompt Dispatcher",
        "mission": "Route les prompts entrants vers l'agent ou le modèle LLM approprié selon contexte.",
        "system_prompt": "Tu es le routeur central de JARVIS. Analyse chaque requête et délègue au bon agent ou backend LLM.",
        "node": "M1",
        "tier": 1,
        "container_name": "jarvis-prompt-dispatcher",
    },
    # Tier 2 — Spécialistes
    {
        "id": "jarvis-trading-sentinel",
        "name": "Trading Sentinel",
        "mission": "Surveillance et exécution trading crypto. Gère MEXC, CoinEx, signaux, alertes.",
        "system_prompt": "Tu es Trading Sentinel. Tu surveilles les marchés crypto, exécutes les ordres autorisés, alertes sur les anomalies.",
        "node": "M1",
        "tier": 2,
        "container_name": "jarvis-trading-sentinel",
    },
    {
        "id": "jarvis-linkedin-safe",
        "name": "LinkedIn Agent",
        "mission": "Automation LinkedIn sécurisée : prospection, messages, connexions. Mode isolé réseau.",
        "system_prompt": "Tu es l'agent LinkedIn de JARVIS. Tu opères en mode safe avec rate limiting strict.",
        "node": "M1",
        "tier": 2,
        "container_name": "jarvis-linkedin-safe",
    },
    {
        "id": "jarvis-omega-bridge",
        "name": "Omega Bridge",
        "mission": "Bridge inter-systèmes. Connecte JARVIS aux APIs externes, passerelle universelle.",
        "system_prompt": "Tu es Omega Bridge. Tu traduis et routages les appels entre systèmes hétérogènes.",
        "node": "M1",
        "tier": 2,
        "container_name": "jarvis-omega-bridge",
    },
    {
        "id": "jarvis-integrity-watchdog",
        "name": "Integrity Watchdog",
        "mission": "Surveillance intégrité système, détection anomalies containers, alertes sécurité.",
        "system_prompt": "Tu es le gardien de l'intégrité JARVIS. Tu monitores, détectes, alertes. Jamais d'action sans validation humaine.",
        "node": "M1",
        "tier": 2,
        "container_name": "jarvis-integrity-watchdog",
    },
    {
        "id": "jarvis-sre",
        "name": "SRE Agent",
        "mission": "Site Reliability: restart auto, health checks, escalade incidents.",
        "system_prompt": "Tu es l'agent SRE JARVIS. Tu maintiens la disponibilité du cluster.",
        "node": "M1",
        "tier": 2,
        "container_name": "jarvis-sre",
    },
    # Tier 3 — Workers
    {
        "id": "jarvis-cowork-dispatcher",
        "name": "Cowork Dispatcher",
        "mission": "Dispatch jobs cowork vers workers disponibles.",
        "system_prompt": "Tu distribues les tâches cowork aux workers libres.",
        "node": "M1",
        "tier": 3,
        "container_name": "jarvis-cowork-dispatcher",
    },
    {
        "id": "jarvis-cowork-loop",
        "name": "Cowork Loop",
        "mission": "Boucle d'exécution jobs cowork répétitifs.",
        "system_prompt": "Tu exécutes les jobs cowork en boucle continue.",
        "node": "M1",
        "tier": 3,
        "container_name": "jarvis-cowork-loop",
    },
    {
        "id": "jarvis-feeder",
        "name": "Feeder",
        "mission": "Ingestion de données externes vers le pipeline JARVIS.",
        "system_prompt": "Tu collectes et normalises les données entrantes.",
        "node": "M1",
        "tier": 3,
        "container_name": "jarvis-feeder",
    },
    {
        "id": "jarvis-cluster-feeder",
        "name": "Cluster Feeder",
        "mission": "Alimente les nœuds M1/M2 avec les jobs LLM distribués.",
        "system_prompt": "Tu dispatches les inférences LLM sur le cluster.",
        "node": "M1",
        "tier": 3,
        "container_name": "jarvis-cluster-feeder",
    },
    {
        "id": "jarvis-library-sync",
        "name": "Library Sync",
        "mission": "Synchronisation bibliothèque documents/mémoire entre nœuds.",
        "system_prompt": "Tu synchronises les assets et la mémoire JARVIS.",
        "node": "M1",
        "tier": 3,
        "container_name": "jarvis-library-sync",
    },
    {
        "id": "jarvis-monitor",
        "name": "Monitor",
        "mission": "Monitoring métriques système, containers, LLM backends.",
        "system_prompt": "Tu collectes et exposes les métriques du cluster JARVIS.",
        "node": "M1",
        "tier": 3,
        "container_name": "jarvis-monitor",
    },
    {
        "id": "jarvis-codex-telegram",
        "name": "Codex Telegram",
        "mission": "Interface Telegram : reçoit commandes, envoie notifications au propriétaire.",
        "system_prompt": "Tu es l'interface Telegram de JARVIS. Tu relaies les commandes et notifications.",
        "node": "M1",
        "tier": 3,
        "container_name": "jarvis-codex-telegram",
    },
    {
        "id": "jarvis-valise-auto",
        "name": "Valise Auto",
        "mission": "Automatisation valise/portfolio : génération contenu, suivi.",
        "system_prompt": "Tu gères les assets portfolio de manière automatisée.",
        "node": "M1",
        "tier": 3,
        "container_name": "jarvis-valise-auto",
    },
]


def gen_ssh_key(agent_id):
    """Génère une paire SSH Ed25519 dédiée à l'agent si absente."""
    key_path = os.path.join(SSH_DIR, f"{agent_id}_ed25519")
    if os.path.exists(key_path):
        return key_path
    os.makedirs(SSH_DIR, exist_ok=True)
    subprocess.run(
        [
            "ssh-keygen",
            "-t",
            "ed25519",
            "-N",
            "",
            "-C",
            f"jarvis-agent-{agent_id}",
            "-f",
            key_path,
        ],
        check=True,
        capture_output=True,
    )
    return key_path


def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    now = datetime.now().isoformat()
    upserted = 0

    for a in AGENTS:
        key_path = gen_ssh_key(a["id"])

        cur.execute(
            """
            INSERT INTO jarvis_agents
              (id, name, mission, system_prompt, node, container_name, tier,
               ssh_key_path, status, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
              name=excluded.name,
              mission=excluded.mission,
              system_prompt=excluded.system_prompt,
              tier=excluded.tier,
              ssh_key_path=excluded.ssh_key_path,
              updated_at=excluded.updated_at
        """,
            (
                a["id"],
                a["name"],
                a["mission"],
                a["system_prompt"],
                a["node"],
                a["container_name"],
                a["tier"],
                key_path,
                "active",
                now,
                now,
            ),
        )
        upserted += 1

    con.commit()
    con.close()
    print(f"[OK] {upserted} agents enregistrés avec clés SSH dans {SSH_DIR}")
    print("[Tier1] Orchestrateurs : jarvis-master, jarvis-prompt-dispatcher")
    print("[Tier2] Spécialistes  : trading, linkedin, omega, integrity, sre")
    print("[Tier3] Workers       : cowork, feeder, library, monitor, codex, valise")


if __name__ == "__main__":
    main()
