#!/usr/bin/env bash
# =============================================================================
# OUVRIR TOUT JARVIS — DÉMARRAGE SIMULTANÉ DE TOUTES LES APPLICATIONS BUREAU
# =============================================================================

# 1. Ouvrir le Dashboard Web Board OS
xdg-open http://127.0.0.1:8766 2>/dev/null || sensible-browser http://127.0.0.1:8766 &

# 2. Ouvrir le Cockpit Master
gnome-terminal --title="⚡ JARVIS COCKPIT MASTER" --geometry=110x35 -- bash -c "/home/pamerys/jarvis/scripts/jarvis_cockpit_menu.sh" &

# 3. Ouvrir l'Application Board OS Dédiée
gnome-terminal --title="🏛️ JARVIS BOARD OS" --geometry=110x35 -- bash -c "/home/pamerys/jarvis/scripts/jarvis_board_app.sh" &

# 4. Ouvrir le Hub Multi-Agents
gnome-terminal --title="🤖 JARVIS AGENTS HUB" --geometry=110x35 -- bash -c "/home/pamerys/jarvis/scripts/jarvis_agents_hub.sh" &
