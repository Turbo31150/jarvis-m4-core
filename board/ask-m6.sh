#!/usr/bin/env bash
# ask-m6.sh — board ask câblé sur M6 (LM Studio 10.42.0.230:1234, câble direct).
# Usage : ./ask-m6.sh <domaine> "<question>"
# Seul modèle chat fiable chargé sur M6 : qwen/qwen3.5-9b (le 14b refuse de se
# charger tant que le 9b occupe la VRAM). Embeddings : Rémi (vectorise_remi).
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

export BOARD_LMS_URL="http://10.42.0.230:1234/v1"
export BOARD_CHAT_MODEL="qwen/qwen3.5-9b"

exec python3 board.py ask "$@"
