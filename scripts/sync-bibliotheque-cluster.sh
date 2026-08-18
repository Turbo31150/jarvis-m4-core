#!/usr/bin/env bash
# Réplique le cœur de la bibliothèque vivante de M1 vers TOUS les nœuds Linux du cluster.
#
# Ne synchronise QUE lib/ + series/ + bloc.sh (~76 Mo) : ~/labo/bibliotheque pèse 284 Go,
# le reste étant des artefacts qui n'ont pas à quitter M1.
# Débit bridé et priorité basse : serveurremjarvis tourne en permanence à ~100 % de charge.
set -uo pipefail

SRC="$HOME/labo/bibliotheque"
LOG="$HOME/jarvis/logs/sync-bibliotheque.log"
mkdir -p "$(dirname "$LOG")"

# alias_ssh:chemin_racine_distant
CIBLES=(
  "remjarvis-server:/home/serveurremjarvis"
  "jarvis-dva:/home/rempc"
)

log() { echo "$(date '+%F %T') $*" >> "$LOG"; }

LOCAL=$(wc -l < "$SRC/lib/BLOCS-INDEX.tsv")
log "=== début sync — référence M1 : $LOCAL blocs ==="
ECHECS=0

for cible in "${CIBLES[@]}"; do
  HOTE="${cible%%:*}"
  RACINE="${cible#*:}"

  # L'arborescence peut disparaître si un home distant est réinitialisé.
  if ! ssh -o BatchMode=yes -o ConnectTimeout=10 "$HOTE" "mkdir -p $RACINE/labo/bibliotheque" 2>>"$LOG"; then
    log "$HOTE : INJOIGNABLE"
    ECHECS=$((ECHECS+1)); continue
  fi

  rsync -az --bwlimit=3000 --timeout=180 -e "ssh -o BatchMode=yes -o ConnectTimeout=10" \
        "$SRC/lib" "$SRC/series" "$HOME/jarvis/bin/bloc.sh" \
        "$HOTE:$RACINE/labo/bibliotheque/" >>"$LOG" 2>&1
  if [ $? -ne 0 ]; then
    log "$HOTE : ÉCHEC rsync"
    ECHECS=$((ECHECS+1)); continue
  fi

  # Contrôle d'identité : un écart de lignes signale une réplication partielle.
  DISTANT=$(ssh -o BatchMode=yes "$HOTE" "wc -l < $RACINE/labo/bibliotheque/lib/BLOCS-INDEX.tsv" 2>/dev/null)
  if [ "$LOCAL" = "$DISTANT" ]; then
    log "$HOTE : OK — $DISTANT blocs"
  else
    log "$HOTE : DIVERGENCE — attendu $LOCAL, trouvé ${DISTANT:-vide}"
    ECHECS=$((ECHECS+1))
  fi
done

log "=== fin — $ECHECS échec(s) sur ${#CIBLES[@]} cible(s) ==="
exit $ECHECS
