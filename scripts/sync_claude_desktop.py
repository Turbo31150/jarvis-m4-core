#!/usr/bin/env python3
import json
import os
import shutil
from pathlib import Path

# Chemins source et cible
CONFIG_DIR_CAP = Path("/home/pamerys/.config/Claude")
CONFIG_DIR_LOW = Path("/home/pamerys/.config/claude")

def enrich_prompt():
    print("=== Enrichissement du MASTER_PROMPT.md ===")
    
    # 1. Charger le MASTER_PROMPT.md de base
    base_prompt_file = CONFIG_DIR_CAP / "MASTER_PROMPT.md"
    if not base_prompt_file.exists():
        print(f"Erreur : MASTER_PROMPT.md introuvable dans {CONFIG_DIR_CAP}")
        return False
        
    base_prompt = base_prompt_file.read_text(encoding="utf-8")
    
    # Trouver où couper ou insérer les nouvelles sections
    # On va insérer nos sections à la fin du document ou après le contenu existant.
    # Pour éviter d'accumuler les ajouts lors de lancements répétés, on nettoie si déjà présent.
    marker = "## ════ CATALOGUE DÉTAILLÉ JARVIS ════"
    if marker in base_prompt:
        base_prompt = base_prompt.split(marker)[0].strip()
        
    # 2. Charger les plugins
    plugins_file = CONFIG_DIR_CAP / "BLOC_2_PLUGINS.txt"
    plugins_content = ""
    if plugins_file.exists():
        plugins_content = plugins_file.read_text(encoding="utf-8")
        # Garder uniquement les lignes non vides et qui ne sont pas des commentaires
        plugins_list = [line.strip() for line in plugins_content.splitlines() if line.strip() and not line.strip().startswith("#")]
        plugins_formatted = "\n".join(f"- {p}" for p in plugins_list)
    else:
        plugins_formatted = "Aucun plugin trouvé."

    # 3. Charger les skills
    skills_file = CONFIG_DIR_CAP / "BLOC_3_SKILLS.txt"
    skills_formatted = ""
    if skills_file.exists():
        skills_lines = skills_file.read_text(encoding="utf-8").splitlines()
        skills_list = []
        for line in skills_lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            skills_list.append(line)
        skills_formatted = "\n".join(f"- {s}" for s in skills_list)
    else:
        skills_formatted = "Aucun skill trouvé."

    # 4. Charger les agents
    agents_file = CONFIG_DIR_CAP / "BLOC_4_AGENTS.txt"
    agents_formatted = ""
    if agents_file.exists():
        agents_lines = agents_file.read_text(encoding="utf-8").splitlines()
        agents_list = []
        for line in agents_lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            agents_list.append(line)
        agents_formatted = "\n".join(f"- {a}" for a in agents_list)
    else:
        agents_formatted = "Aucun agent trouvé."

    # 5. Charger la configuration des serveurs MCP pour lister leurs outils ou connecteurs
    config_file = CONFIG_DIR_CAP / "claude_desktop_config.json"
    mcp_servers_list = []
    if config_file.exists():
        try:
            config_data = json.loads(config_file.read_text(encoding="utf-8"))
            mcp_servers = config_data.get("mcpServers", {})
            for name, srv in mcp_servers.items():
                cmd = srv.get("command", "")
                args = " ".join(srv.get("args", []))
                mcp_servers_list.append(f"| **{name}** | `{cmd} {args}` |")
        except Exception as e:
            print(f"Erreur lecture config json: {e}")
    
    mcp_formatted = "\n".join(mcp_servers_list) if mcp_servers_list else "Aucun serveur MCP configuré."

    # 6. Assembler le nouveau prompt
    enriched_prompt = f"""{base_prompt}

## {marker}
Ce catalogue décrit l'ensemble des capacités de votre environnement JARVIS local. Utilisez ces informations pour déléguer les tâches aux bons connecteurs, agents ou compétences.

### 🔌 SERVEURS MCP CONFIGURÉS (33)
Ces serveurs sont configurés et connectés dans Claude Desktop. Vous pouvez appeler leurs outils directement.

| Nom du Serveur | Commande / Connecteur |
| --- | --- |
{mcp_formatted}

### 🧩 PLUGINS Claude Code (57)
Ces plugins étendent vos capacités de traitement :
{plugins_formatted}

### 🛠️ COMPÉTENCES / SKILLS INDIVIDUELS PERSISTANTS (186)
Vous pouvez invoquer ou vous inspirer de ces compétences existantes pour exécuter les instructions de l'utilisateur :
{skills_formatted}

### 🤖 AGENTS SPÉCIALISÉS INVOCABLES (147)
Vous pouvez déléguer des tâches entières ou parallèles à ces agents via l'outil `invoke_agent` de `jarvis-agents` (ex: `jarvis-agents · invoke_agent {{"agent_id": "nom-agent", "message": "tâche"}}`) :
{agents_formatted}
"""

    # 7. Écrire le prompt final
    (CONFIG_DIR_CAP / "MASTER_PROMPT.md").write_text(enriched_prompt, encoding="utf-8")
    print(f"✓ Écrit {CONFIG_DIR_CAP}/MASTER_PROMPT.md")
    
    # Créer le dossier minuscule s'il n'existe pas
    CONFIG_DIR_LOW.mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR_LOW / "MASTER_PROMPT.md").write_text(enriched_prompt, encoding="utf-8")
    print(f"✓ Écrit {CONFIG_DIR_LOW}/MASTER_PROMPT.md")
    
    return True

def sync_config():
    print("=== Synchronisation de claude_desktop_config.json ===")
    src_file = CONFIG_DIR_CAP / "claude_desktop_config.json"
    dst_file = CONFIG_DIR_LOW / "claude_desktop_config.json"
    
    if not src_file.exists():
        print(f"Erreur : {src_file} introuvable.")
        return False
        
    try:
        shutil.copy2(src_file, dst_file)
        print(f"✓ Copié {src_file} vers {dst_file}")
    except shutil.SameFileError:
        print(f"✓ {dst_file} est déjà lié symboliquement ou identique à {src_file} (aucune copie nécessaire)")
    return True

if __name__ == "__main__":
    success_prompt = enrich_prompt()
    success_config = sync_config()
    if success_prompt and success_config:
        print("=== SYNCHRONISATION CLAUDE DESKTOP COMPLÈTE ET RÉUSSIE ===")
    else:
        print("=== ERREUR DURANT LA SYNCHRONISATION ===")
