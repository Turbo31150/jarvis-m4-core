#!/usr/bin/env bash
# Rédige et livre les 72 formations dans Notion, sans surveillance.
#
# Détaché de toute session (setsid) : survit à la fermeture du terminal.
# Le pipeline étant idempotent, chaque cycle ne reprend que ce qui manque.
#
# Le backend cloud est plafonné : 50 formations ont échoué d'affilée en
# HTTP 429 le 14/08. Un échec n'est donc pas une panne mais une attente —
# on réarme les 429 et on repasse plus tard, au lieu de les abandonner.
set -uo pipefail

PIPE=/home/pamerys/jarvis/scripts/notion_formations_pipeline.py
DB=/home/pamerys/jarvis/data/formations_contenu.db
PAUSE_QUOTA=${PAUSE_QUOTA:-900}   # 15 min avant de retenter après un 429

reste() { sqlite3 "$DB" "select count(*) from contenu where markdown is null;"; }

while :; do
  r=$(reste)
  if [ "$r" -eq 0 ]; then
    python3 "$PIPE" push --limit 100
    echo "[$(date +%H:%M)] ✓ 72/72 rédigées et livrées dans Notion"
    break
  fi

  echo "[$(date +%H:%M)] cycle — $r formation(s) à rédiger"
  FORMATIONS_BACKEND=cloud python3 "$PIPE" generate --limit 8 --workers 3
  python3 "$PIPE" push --limit 20

  # Un 429 ne condamne pas la formation : on efface la marque d'échec pour
  # que le cycle suivant la reprenne, et on laisse le quota se recharger.
  quota=$(sqlite3 "$DB" "select count(*) from contenu where erreur like '%429%';")
  if [ "$quota" -gt 0 ]; then
    sqlite3 "$DB" "update contenu set erreur=null where erreur like '%429%';"
    echo "[$(date +%H:%M)] quota atteint ($quota) — pause ${PAUSE_QUOTA}s"
    sleep "$PAUSE_QUOTA"
  else
    sleep 30
  fi
done
