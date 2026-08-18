#!/usr/bin/env bash
# ask-remi.sh — board ask câblé sur Rémi (Ollama Tailscale 100.113.121.61:11434).
# Fallback quand M6 (câble direct) est injoignable.
# Usage : ./ask-remi.sh <domaine> "<question>"
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

export BOARD_LMS_URL="http://100.113.121.61:11434/v1"
export BOARD_CHAT_MODEL="gemma3:27b"

exec python3 board.py ask "$@"
