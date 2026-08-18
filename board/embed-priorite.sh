#!/usr/bin/env bash
# Vectorisation du board ordonnée par valeur d'usage — backend Rémi (0 token).
# Résumable : ne traite que les chunks sans embedding. Relancer = reprendre.
set -u
cd /home/pamerys/jarvis/board
export BOARD_LMS_URL="${BOARD_LMS_URL:-http://100.113.121.61:11434/v1}"
export BOARD_EMBED_MODEL="${BOARD_EMBED_MODEL:-nomic-embed-text:latest}"
export BOARD_EMBED_PAR="${BOARD_EMBED_PAR:-6}"
export BOARD_EMBED_LOT="${BOARD_EMBED_LOT:-32}"

ORDRE="cluster-m1 fiabilite-exploitation inference-locale rag-retrieval contrat-gama2 donnees-persistance cout-energie orchestration-agents souverainete biblio-vivante"

for d in $ORDRE; do
  echo "════ domaine: $d — $(date '+%H:%M:%S') ════"
  python3 board.py embed --domain "$d" --limit 200000
done
echo "════ terminé $(date '+%H:%M:%S') ════"
