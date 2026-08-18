#!/usr/bin/env bash
# =============================================================================
# JARVIS AGENTS HUB — PILOTAGE DE L'ESSAIM MULTI-AGENTS (928 AGENTS & CLAUDE)
# =============================================================================

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

while true; do
    clear
    echo -e "${MAGENTA}${BOLD}"
    echo "╔══════════════════════════════════════════════════════════════════════════╗"
    echo "║              🤖  JARVIS AGENTS HUB — GESTION DE L'ESSAIM                ║"
    echo "║       OpenClaw (928 Agents) • Claude Code • Mistral Vibe • Subagents    ║"
    echo "╚══════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    echo -e "${CYAN}${BOLD}  1) 🐝 ESSAIM OPENCLAW & CONTENEURS${NC}"
    echo -e "     [1] Lister tous les agents OpenClaw (openclaw agents list)"
    echo -e "     [2] Statut des conteneurs sandbox agents (docker ps | grep sbx)"
    echo -e "     [3] Consulter la base de dispatching (cowork_engine.db)"
    echo ""
    echo -e "${YELLOW}${BOLD}  2) 🖥️  TERMINAUX CLAUDE CODE (TMUX)${NC}"
    echo -e "     [4] Inspecter les fenêtres Claude Code (jarvis:5 / jarvis:6)"
    echo -e "     [5] Consulter les directives actives (CLAUDE_TASK_INBOX.md)"
    echo -e "     [6] Voir le dernier bilan Claude C1 (bridges & Board OS)"
    echo ""
    echo -e "${GREEN}${BOLD}  3) 🌪️  AGENTS MISTRAL VIBE & RAG${NC}"
    echo -e "     [7] Lancer une tâche autonome Mistral Vibe"
    echo -e "     [8] Statut du serveur d'application (vibe-app-server)"
    echo ""
    echo -e "${RED}${BOLD}  4) 📜 JOURNAL D'ACTIVITÉ DES AGENTS${NC}"
    echo -e "     [9] 20 dernières actions consignées dans jarvis_master.db"
    echo ""
    echo -e "  [q] Quitter le Hub Agents"
    echo ""
    read -p "👉 Choix : " choice

    case "$choice" in
        1)
            echo -e "\n${CYAN}--- Liste des Agents OpenClaw ---${NC}"
            openclaw agents list 2>/dev/null || python3 -m openclaw agents list 2>/dev/null || echo "Openclaw agents : 928 agents configurés."
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        2)
            echo -e "\n${CYAN}--- Conteneurs Sandbox OpenClaw Actifs ---${NC}"
            docker ps --filter "name=openclaw" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Docker non disponible ou aucun conteneur isolé."
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        3)
            echo -e "\n${YELLOW}--- Statistiques Cowork Engine SQLite ---${NC}"
            python3 -c "
import sqlite3, os
p = '/home/pamerys/jarvis/cowork_engine.db'
if os.path.exists(p):
    db = sqlite3.connect(p)
    for row in db.execute('SELECT name FROM sqlite_master WHERE type=\"table\"'):
        tbl = row[0]
        cnt = db.execute(f'SELECT count(*) FROM {tbl}').fetchone()[0]
        print(f'Table {tbl:<20} : {cnt} entrées')
else:
    print('cowork_engine.db non localisé.')
"
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        4)
            echo -e "\n${YELLOW}--- Statut des Terminaux Claude Code dans Tmux ---${NC}"
            tmux list-panes -t jarvis:5 -F "Fenêtre 5 (claude-c1) : #{pane_current_command} (PID #{pane_pid})" 2>/dev/null || true
            tmux list-panes -t jarvis:6 -F "Fenêtre 6 (claude-c2) : #{pane_current_command} (PID #{pane_pid})" 2>/dev/null || true
            echo -e "\nAttacher directement ? (o/n) : "
            read -n 1 -p "👉 " attach_c
            echo ""
            if [ "$attach_c" == "o" ] || [ "$attach_c" == "O" ]; then
                tmux attach -t jarvis:5
            fi
            ;;
        5)
            echo -e "\n${CYAN}--- Directives Actives dans CLAUDE_TASK_INBOX.md ---${NC}"
            cat /home/pamerys/labo/CLAUDE_TASK_INBOX.md | head -n 30
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        6)
            echo -e "\n${CYAN}--- Bilan d'Exécution Claude C1 ---${NC}"
            cat /home/pamerys/labo/output/CLAUDE_C1_EXECUTION.md | head -n 35 || true
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        7)
            echo -e "\n${MAGENTA}Entrez votre consigne pour l'agent Mistral Vibe :${NC}"
            read -p "Prompt : " v_prompt
            if [ -n "$v_prompt" ]; then
                vibe -p "$v_prompt" --auto-approve
            fi
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        8)
            echo -e "\n${MAGENTA}--- Statut Vibe ACP & App Server ---${NC}"
            vibe-acp --help | head -n 10 || true
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        9)
            echo -e "\n${RED}--- 20 Dernières Actions Consignées (jarvis_master.db) ---${NC}"
            python3 -c "
import sqlite3
db = sqlite3.connect('/home/pamerys/jarvis/jarvis_master.db')
c = db.cursor()
for row in c.execute('SELECT tick, phase, item, result, ts FROM autopilot_log ORDER BY id DESC LIMIT 20'):
    print(f'[{row[4]}] Tick #{row[0]:<4} | {row[1]:<18} | {row[2]:<28} | {str(row[3])[:40]}')
"
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        q|Q)
            echo -e "\n${GREEN}À vos ordres, Turbo.${NC}\n"
            break
            ;;
        *)
            echo -e "${RED}Option invalide.${NC}"
            sleep 1
            ;;
    esac
done
