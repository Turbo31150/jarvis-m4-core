#!/usr/bin/env bash
# =============================================================================
# JARVIS COCKPIT — MENU INTERACTIF MAÎTRE & HUBS OPÉRATIONNELS (ORFÈVRERIE)
# =============================================================================

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

while true; do
    clear
    echo -e "${CYAN}${BOLD}"
    echo "╔══════════════════════════════════════════════════════════════════════════╗"
    echo "║                  🏛️  JARVIS OS — COCKPIT GÉNÉRAL                        ║"
    echo "║         Orchestrateur H24 • Board OS • Claude Code • Mistral AI          ║"
    echo "╚══════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${YELLOW}${BOLD}  1) 🏛️  BOARD OS, IA LOCALE & CLAUDE CODE${NC}"
    echo -e "     [1] Attacher la session Tmux JARVIS (7 Fenêtres : Réveil, Board, Claude C1/C2)"
    echo -e "     [2] Diagnostic Board OS & Corpus (87k chunks)"
    echo -e "     [3] Poser une question au Conseil d'Experts (Consensus)"
    echo -e "     [4] Lancer une session Claude Code autonome"
    echo -e "     [5] Consulter le dernier rapport de supervision"
    echo ""
    echo -e "${MAGENTA}${BOLD}  2) 🌪️  MISTRAL AI SUITE (VIBE, RAG & WORKFLOWS)${NC}"
    echo -e "     [6] Lancer Mistral Vibe (CLI Agentic Coding)"
    echo -e "     [7] Poser une question RAG sur document (mistral-rag)"
    echo -e "     [8] Ouvrir le projet Mistral Workflows (laboratoire)"
    echo ""
    echo -e "${GREEN}${BOLD}  3) ⏰ MINUTEUR RÉVEIL, NOTION & ACTIONS MASSIVES${NC}"
    echo -e "     [9] Statut & Contrôle du Minuteur Réveil (jarvis-reveil)"
    echo -e "     [a] Forcer la synchronisation Notion ⇄ Claude Code"
    echo -e "     [b] Ouvrir le dossier Candidature FMS Toulouse RQTH"
    echo ""
    echo -e "${BLUE}${BOLD}  4) 🌐 WEB DASHBOARDS & BRIDGES LOCAUX${NC}"
    echo -e "     [c] Ouvrir Lumen Transcription (http://127.0.0.1:4173)"
    echo -e "     [d] Ouvrir Whisper Voice UI (http://127.0.0.1:9742)"
    echo -e "     [e] Ouvrir Hub LLM Models 18800 (http://127.0.0.1:18800/v1/models)"
    echo ""
    echo -e "${RED}${BOLD}  5) 💾 STOCKAGE, CLUSTER & SYSTÈME${NC}"
    echo -e "     [f] Statut Disques & Partitions NVMe (df -h)"
    echo -e "     [g] Diagnostic Lien Direct USB-C M1 (10.42.0.230 - 1.4 ms)"
    echo -e "     [h] Moniteur Système (top)"
    echo ""
    echo -e "  [q] Quitter le Cockpit"
    echo ""
    read -p "👉 Choix : " choice

    case "$choice" in
        1)
            tmux attach -t jarvis || tmux new-session -s jarvis
            ;;
        2)
            echo -e "\n${CYAN}--- Diagnostic Board OS & Intégrité SQLite ---${NC}"
            python3 -c "
import sqlite3
db = sqlite3.connect('/home/pamerys/jarvis/databases/board.db')
c = db.cursor()
c.execute('PRAGMA quick_check;')
print('Quick Check:', c.fetchone()[0])
c.execute('SELECT COUNT(*) FROM chunks;')
print('Total Chunks:', c.fetchone()[0])
c.execute('SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL;')
print('Vectorisés:', c.fetchone()[0])
"
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        3)
            echo -e "\n${YELLOW}Entrez votre question pour le Conseil d'Experts :${NC}"
            read -p "Question : " q_user
            if [ -n "$q_user" ]; then
                board ask --domain jarvis --mode consensus "$q_user" 2>/dev/null || python3 -m jarvis.cli.board ask "$q_user" 2>/dev/null || echo "Interrogation terminée."
            fi
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        4)
            echo -e "\n${CYAN}Lancement de Claude Code dans /home/pamerys/labo...${NC}"
            cd /home/pamerys/labo && claude
            ;;
        5)
            echo -e "\n${CYAN}--- Dernier Rapport de Supervision ---${NC}"
            cat /home/pamerys/labo/output/ORCHESTRATEUR_RAPPORT_ACTIF.md | head -n 35 || true
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        6)
            echo -e "\n${MAGENTA}Lancement de Mistral Vibe...${NC}"
            vibe --help
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        7)
            echo -e "\n${MAGENTA}Entrez le chemin du fichier et votre question :${NC}"
            read -p "Chemin du fichier (PDF/TXT/MD) : " doc_path
            read -p "Question : " doc_q
            if [ -n "$doc_path" ] && [ -n "$doc_q" ]; then
                mistral-rag -f "$doc_path" -q "$doc_q"
            fi
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        8)
            echo -e "\n${MAGENTA}Ouverture du répertoire Mistral Workflows...${NC}"
            cd /home/pamerys/labo/mistral-workflow && make check
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        9)
            echo -e "\n${GREEN}--- Statut du Minuteur Réveil ---${NC}"
            jarvis-reveil status || python3 /home/pamerys/jarvis/scripts/jarvis_reveil_minuteur.py status
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        a|A)
            echo -e "\n${YELLOW}Synchronisation Notion ⇄ Claude Code en cours...${NC}"
            python3 /home/pamerys/jarvis/scripts/jarvis_notion_claude_bridge.py
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        b|B)
            echo -e "\n${CYAN}--- Dossier FMS Toulouse RQTH ---${NC}"
            cat /home/pamerys/labo/output/CANDIDATURE_FMS_TOULOUSE_RQTH.md | head -n 40 || true
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        c|C)
            echo -e "\n${CYAN}Ouverture de Lumen Transcription...${NC}"
            xdg-open http://127.0.0.1:4173 2>/dev/null || sensible-browser http://127.0.0.1:4173 &
            sleep 1
            ;;
        d|D)
            echo -e "\n${CYAN}Ouverture de Whisper Voice UI...${NC}"
            xdg-open http://127.0.0.1:9742 2>/dev/null || sensible-browser http://127.0.0.1:9742 &
            sleep 1
            ;;
        e|E)
            echo -e "\n${CYAN}Ouverture du catalogue Hub LLM 18800...${NC}"
            curl -s http://127.0.0.1:18800/v1/models | jq . 2>/dev/null || curl -s http://127.0.0.1:18800/v1/models
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        f|F)
            echo -e "\n${GREEN}--- Espace Disque & Partitions ---${NC}"
            df -h
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        g|G)
            echo -e "\n${CYAN}--- Ping du lien direct M1 (10.42.0.230) ---${NC}"
            ping -c 3 10.42.0.230 || echo "Lien M1 non joignable via 10.42.0.230"
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        h|H)
            top
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
