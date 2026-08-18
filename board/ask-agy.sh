#!/usr/bin/env bash
# ask-agy.sh — board ask cable sur agy (CLI Antigravity) via le shim OpenAI.
# Usage : ./ask-agy.sh <domaine> "<question>" [--experts a,b]
#
# Repartition deliberee des deux backends :
#   CHAT       -> shim agy 127.0.0.1:18811 (Gemini / Claude / GPT-OSS)
#   EMBEDDINGS -> M6 10.42.0.230:1234 (nomic, dim 768) — agy n'expose pas
#                 d'embeddings, et la base est vectorisee en 768 : changer de
#                 modele d'embedding invaliderait les 83 000 vecteurs.
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

SHIM_PORT="${AGY_SHIM_PORT:-18811}"
export BOARD_CHAT_URL="http://127.0.0.1:${SHIM_PORT}/v1"
# MEME PIEGE que BOARD_LMS_URL ci-dessous, et il mordait ici aussi :
# BOARD_CHAT_MODEL est deja posee dans l'environnement du shell (valeur heritee
# « qwen3:1.7b »), donc ce defaut ne prenait JAMAIS. Le shim, lui, ne refuse pas
# un modele inconnu : il repond avec le sien. Consequence mesuree 2026-08-17 :
# Gemini repondait, mais `answers.model` enregistrait « qwen3:1.7b » — la table
# mentait sur QUI a vote, ce que ce board est precisement cense empecher.
# Le choix du modele passe par une variable dediee, non polluee.
export BOARD_CHAT_MODEL="${AGY_MODEL:-gemini-3.7-flash-medium}"
# Les modeles affectes par expert en base sont ceux du parc LOCAL et n'existent
# pas derriere le shim : sans ce forcage, chaque expert ainsi affecte fausse a
# nouveau la tracabilite du vote.
export BOARD_FORCE_MODEL="${BOARD_FORCE_MODEL:-1}"
# NE PAS ecrire ${BOARD_LMS_URL:-...} : cette variable est deja posee dans
# l'environnement du shell (valeur heritee http://127.0.0.1:11434/v1, un
# Ollama local absent de M4). Le defaut n'aurait alors jamais pris, et les
# embeddings partaient dans le vide -> « voie vectorielle HORS SERVICE ».
# L'override se fait par une variable dediee, non polluee.
export BOARD_LMS_URL="${BOARD_EMBED_URL:-http://10.42.0.230:1234/v1}"
export BOARD_EMBED_MODEL="${BOARD_EMBED_MODEL:-text-embedding-nomic-embed-text-v1.5}"

# Le shim est local et peu couteux a relancer : le demarrer s'il dort.
if ! curl -s -m 3 -o /dev/null "${BOARD_CHAT_URL}/models"; then
  echo "ask-agy: shim absent sur :${SHIM_PORT}, demarrage..." >&2
  nohup python3 "$HOME/jarvis/bin/agy-openai-shim.py" "$SHIM_PORT" \
    >>"$HOME/jarvis/logs/agy-shim.log" 2>&1 &
  for _ in $(seq 1 10); do
    sleep 1
    curl -s -m 2 -o /dev/null "${BOARD_CHAT_URL}/models" && break
  done
  curl -s -m 2 -o /dev/null "${BOARD_CHAT_URL}/models" || {
    echo "ask-agy: shim injoignable, voir ~/jarvis/logs/agy-shim.log" >&2; exit 1; }
fi

# Embeddings : avertir sans bloquer. Le board sait degrader en FTS5 seul.
curl -s -m 4 -o /dev/null "${BOARD_LMS_URL}/models" \
  || echo "ask-agy: ATTENTION embeddings M6 injoignables -> recherche lexicale seule" >&2

exec python3 board.py ask "$@"
