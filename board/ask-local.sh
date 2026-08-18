#!/usr/bin/env bash
# ask-local.sh — board ask câblé sur Ollama local M4 (dernier recours).
# Utilisé quand M6 (câble direct) est injoignable ET Rémi trop lent (modèle non résident).
# Usage : ./ask-local.sh <domaine> "<question>"
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

export BOARD_LMS_URL="http://127.0.0.1:11434/v1"
export BOARD_CHAT_MODEL="gemma3:4b"

exec python3 board.py ask "$@"
