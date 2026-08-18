#!/usr/bin/env bash
# ask-mistral.sh — board ask câblé sur l'API Mistral (api.mistral.ai, OpenAI-compatible).
# Usage : ./ask-mistral.sh <domaine> "<question>" [--experts a,b]
#
# Place dans la cascade : backend CLOUD, donc APRÈS le local (LOI 2 — 0-token
# d'abord). À réserver aux arbitrages où les modèles locaux calent : gros
# contexte, code lourd (Codestral/Devstral), multilingue fin.
#
# Répartition des deux voies, comme ask-agy.sh :
#   CHAT       -> Mistral (cloud, facturé au token)
#   EMBEDDINGS -> M6 10.42.0.230:1234, nomic dim 768 — NE PAS basculer sur
#                 mistral-embed (dim 1024) : les ~83 000 vecteurs de board.db
#                 sont en 768 et deviendraient inexploitables.
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

# Clé hors git (chmod 600). Jamais en dur ici : ce fichier peut partir en dépôt.
ENVF="${MISTRAL_ENV_FILE:-$HOME/.config/jarvis/mistral.env}"
if [ -z "${MISTRAL_API_KEY:-}" ]; then
  [ -r "$ENVF" ] || { echo "❌ clé absente : $ENVF introuvable (MISTRAL_API_KEY=…)" >&2; exit 1; }
  # shellcheck disable=SC1090
  . "$ENVF"
fi
[ -n "${MISTRAL_API_KEY:-}" ] || { echo "❌ MISTRAL_API_KEY vide dans $ENVF" >&2; exit 1; }

export BOARD_CHAT_URL="https://api.mistral.ai/v1"
export BOARD_API_KEY="$MISTRAL_API_KEY"    # c'est CE nom que board.py::_post lit
export BOARD_FORCE_MODEL=1   # les modeles affectes en base sont locaux, inexistants chez Mistral
export BOARD_CHAT_API="chat"   # Mistral ne sert que /v1/chat/completions
# NE PAS ecrire ${BOARD_CHAT_MODEL:-...} : cette variable est DEJA posee dans
# l'environnement du shell (valeur heritee qwen3:1.7b, un modele local). Le
# defaut ne prenait donc jamais et les 4 experts partaient en « Invalid model:
# qwen3:1.7b » cote Mistral. Le choix du modele passe par une variable dediee.
export BOARD_CHAT_MODEL="${MISTRAL_MODEL:-mistral-medium-latest}"

# Même piège que dans ask-agy.sh : BOARD_LMS_URL est déjà posée dans
# l'environnement du shell (Ollama absent de M4) — on force la voie embeddings
# par une variable dédiée, sinon la vectorielle part dans le vide.
export BOARD_LMS_URL="${BOARD_EMBED_URL:-http://10.42.0.230:1234/v1}"
export BOARD_EMBED_MODEL="${BOARD_EMBED_MODEL:-text-embedding-nomic-embed-text-v1.5}"

exec python3 board.py ask "$@"
