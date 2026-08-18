#!/usr/bin/env bash
# ask-hub.sh — board branché sur le HUB unifié :18800 (au lieu de M6 en direct).
# Gain vitesse : le hub cascade M6 → gemma3:4b, donc plus de stall quand M6
# évince son modèle chat. Modèle logique 'jarvis-fast' = le plus rapide dispo.
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"
export BOARD_LMS_URL="http://127.0.0.1:18800/v1"
export BOARD_CHAT_MODEL="jarvis-fast"
exec python3 board.py ask "$@"
