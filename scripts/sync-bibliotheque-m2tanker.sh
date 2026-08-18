#!/usr/bin/env bash
# Réplique le cœur de la bibliothèque vivante de M1 vers le nœud M2_TANKER (serveurremjarvis).
#
# Ne synchronise QUE lib/ + series/ (~76 Mo) : ~/labo/bibliotheque pèse 284 Go au total,
# le reste étant des artefacts qui n'ont pas à quitter M1.
# Débit bridé : la cible tourne en permanence à ~100 % de charge (4 vCPU).
set -uo pipefail

SRC="$HOME/labo/bibliotheque"
DEST_HOST="remjarvis-server"          # alias ~/.ssh/config — Tailscale SSH, non interactif
DEST="\$HOME/labo/bibliotheque/"
LOG="$HOME/jarvis/logs/sync-bibliotheque.log"
mkdir -p "$(dirname "$LOG")"

log() { echo "$(date '+%F %T') $*" >> "$LOG"; }

log "=== début sync bibliothèque ==="

# L'arborescence peut disparaître si le home distant est réinitialisé.
ssh -o BatchMode=yes -o ConnectTimeout=10 "$DEST_HOST" 'mkdir -p ~/labo/bibliotheque ~/bin' \
  || { log "ÉCHEC: cible injoignable"; exit 1; }

rsync -az --bwlimit=3000 --timeout=180 -e "ssh -o BatchMode=yes -o ConnectTimeout=10" \
      "$SRC/lib" "$SRC/series" "$DEST_HOST:~/labo/bibliotheque/" >>"$LOG" 2>&1
RC=$?
[ $RC -ne 0 ] && { log "ÉCHEC rsync (code $RC)"; exit $RC; }

rsync -az --bwlimit=3000 -e "ssh -o BatchMode=yes" "$HOME/jarvis/bin/bloc.sh" \
      "$DEST_HOST:~/bin/" >>"$LOG" 2>&1

# Contrôle d'identité : un écart de lignes signale une réplication partielle.
LOCAL=$(wc -l < "$SRC/lib/BLOCS-INDEX.tsv")
REMOTE=$(ssh -o BatchMode=yes "$DEST_HOST" 'wc -l < ~/labo/bibliotheque/lib/BLOCS-INDEX.tsv' 2>/dev/null)

if [ "$LOCAL" = "$REMOTE" ]; then
  log "OK — $LOCAL blocs identiques sur les 2 nœuds"
else
  log "DIVERGENCE — M1=$LOCAL vs M2T=$REMOTE"
  exit 2
fi
