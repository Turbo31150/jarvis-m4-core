#!/usr/bin/env bash
# =============================================================================
# JARVIS BOARD OS — APPLICATION BUREAU DÉDIÉE (CONSEIL D'EXPERTS & BIBLIOTHÈQUE)
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
    echo -e "${CYAN}${BOLD}"
    echo "╔══════════════════════════════════════════════════════════════════════════╗"
    echo "║            🏛️  JARVIS BOARD OS — APPLICATION BUREAU DÉDIÉE               ║"
    echo "║       Conseil d'Experts • Bibliothèque Vivante • 87 448 Chunks           ║"
    echo "╚══════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    echo -e "${YELLOW}${BOLD}  1) 🌐 INTERFACE GRAPHIQUE & DASHBOARD${NC}"
    echo -e "     [1] Ouvrir le Dashboard Web Board OS (http://127.0.0.1:8766)"
    echo -e "     [2] Diagnostic de santé complet (Board Doctor)"
    echo -e "     [3] Statistiques des 13 domaines et de la vectorisation"
    echo ""
    echo -e "${GREEN}${BOLD}  2) 🏛️  CONSULTATION DES EXPERTS EN DIRECT${NC}"
    echo -e "     [4] Poser une question en mode CONSENSUS (tous les experts)"
    echo -e "     [5] Lancer un DÉBAT contradictoire entre experts"
    echo -e "     [6] Recherche sémantique / lexicale dans les 87k chunks"
    echo ""
    echo -e "${MAGENTA}${BOLD}  3) 🔄 ARBITRAGE & SUPERVISION${NC}"
    echo -e "     [7] Voir le flux d'arbitrage en direct (tmux jarvis:3)"
    echo -e "     [8] Consulter le dernier rapport de supervision"
    echo ""
    echo -e "  [q] Quitter Board OS"
    echo ""
    read -p "👉 Choix : " choice

    case "$choice" in
        1)
            echo -e "\n${CYAN}Ouverture du Dashboard Web...${NC}"
            xdg-open http://127.0.0.1:8766 2>/dev/null || sensible-browser http://127.0.0.1:8766 &
            sleep 1
            ;;
        2)
            echo -e "\n${CYAN}--- Diagnostic Board OS (Doctor) ---${NC}"
            python3 /home/pamerys/jarvis/board/board.py doctor 2>/dev/null || board doctor
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        3)
            echo -e "\n${CYAN}--- Statistiques de la Base de Connaissances ---${NC}"
            python3 -c "
import sqlite3
db = sqlite3.connect('/home/pamerys/jarvis/databases/board.db')
c = db.cursor()
total = c.execute('SELECT count(*) FROM chunks').fetchone()[0]
vec = c.execute('SELECT count(*) FROM chunks WHERE embedding IS NOT NULL').fetchone()[0]
sources = c.execute('SELECT count(DISTINCT source_file) FROM chunks').fetchone()[0]
print(f'Chunks Totaux : {total:,}')
print(f'Vectorisés    : {vec:,} ({vec/total*100:.2f}%)')
print(f'Fichiers Sources : {sources:,}')
"
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        4)
            echo -e "\n${YELLOW}Entrez votre question pour le Conseil d'Experts (Consensus) :${NC}"
            read -p "Question : " q_user
            if [ -n "$q_user" ]; then
                python3 /home/pamerys/jarvis/board/board.py ask --mode consensus "$q_user" 2>/dev/null || board ask --mode consensus "$q_user"
            fi
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        5)
            echo -e "\n${YELLOW}Entrez le sujet du Débat contradictoire :${NC}"
            read -p "Sujet : " d_user
            if [ -n "$d_user" ]; then
                python3 /home/pamerys/jarvis/board/board.py debate "$d_user" 2>/dev/null || board debate "$d_user"
            fi
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        6)
            echo -e "\n${CYAN}Recherche lexicale FTS5 / Sémantique :${NC}"
            read -p "Mots-clés : " s_query
            if [ -n "$s_query" ]; then
                python3 -c "
import sqlite3
db = sqlite3.connect('/home/pamerys/jarvis/databases/board.db')
c = db.cursor()
rows = c.execute('SELECT source_file, substr(content, 1, 150) FROM chunks WHERE content MATCH ? LIMIT 5', ('\"' + '$s_query' + '\"',)).fetchall()
if not rows:
    rows = c.execute('SELECT source_file, substr(content, 1, 150) FROM chunks WHERE content LIKE ? LIMIT 5', ('%' + '$s_query' + '%',)).fetchall()
print(f'Résultats pour « $s_query » ({len(rows)} affichés) :')
for sf, txt in rows:
    print(f'  • [{sf}] : {txt.strip()}...')
"
            fi
            echo -e "\n${GREEN}Appuyez sur Entrée pour continuer...${NC}"
            read
            ;;
        7)
            echo -e "\n${CYAN}Attachement à la session de débat continu (jarvis:3)...${NC}"
            tmux attach -t jarvis:3
            ;;
        8)
            echo -e "\n${CYAN}--- Dernier Rapport de Supervision ---${NC}"
            cat /home/pamerys/labo/output/ORCHESTRATEUR_RAPPORT_ACTIF.md | head -n 35 || true
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
