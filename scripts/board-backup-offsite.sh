#!/usr/bin/env bash
# board-backup-offsite.sh — Sauvegarde quotidienne du board d'experts (board.db)
# vers M6 (ssh m1 → ~/backups/board) + SSD M1 USB (/media/pamerys/JARVIS-M1/data/backups/board).
# Snapshot atomique SQLite (compatible WAL/écriture en cours), gzip, sha256 vérifié
# côté destination, rotation KEEP par cible. Chaque cible est fail-safe : une
# destination absente (M6 éteint, SSD débranché) est skippée sans faire échouer le run.
set -uo pipefail

BOARD_DB="${BOARD_DB:-$HOME/jarvis/board/board.db}"
LOCAL_DIR="${LOCAL_DIR:-$HOME/jarvis/backups/board}"
USB_DIR="/media/pamerys/JARVIS-M1/data/backups/board"
M6_HOST="m1"                       # alias ssh → 10.42.0.230 (user turbo, clé jarvis_cluster)
M6_DIR="backups/board"
KEEP="${KEEP:-7}"
TS="$(date +%Y%m%d_%H%M)"
NAME="board_${TS}.db"
LOG="$HOME/jarvis/logs/board-backup.log"
mkdir -p "$LOCAL_DIR" "$(dirname "$LOG")"

log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }

# Verrou anti-chevauchement
exec 9>"$LOCAL_DIR/.lock"
flock -n 9 || { log "run déjà en cours, abandon"; exit 0; }

[ -f "$BOARD_DB" ] || { log "ERREUR: $BOARD_DB introuvable"; exit 1; }

# 1. Snapshot atomique + compression + empreinte
sqlite3 "$BOARD_DB" ".backup '$LOCAL_DIR/$NAME'" || { log "ERREUR snapshot"; exit 1; }
gzip -1 -f "$LOCAL_DIR/$NAME"
GZ="$NAME.gz"
SUM="$(sha256sum "$LOCAL_DIR/$GZ" | awk '{print $1}')"
echo "$SUM  $GZ" > "$LOCAL_DIR/$GZ.sha256"
log "snapshot $GZ ($(du -h "$LOCAL_DIR/$GZ" | cut -f1)) sha256=$SUM"

rotate() { ls -1t "$1"/board_*.db.gz 2>/dev/null | tail -n +$((KEEP+1)) | while read -r f; do rm -f "$f" "$f.sha256"; done; }

# 2. → M6 (vérif sha256 distante)
if ssh -o BatchMode=yes -o ConnectTimeout=6 "$M6_HOST" "mkdir -p $M6_DIR" 2>/dev/null; then
  if scp -q "$LOCAL_DIR/$GZ" "$LOCAL_DIR/$GZ.sha256" "$M6_HOST:$M6_DIR/" \
     && ssh "$M6_HOST" "cd $M6_DIR && sha256sum -c $GZ.sha256 >/dev/null"; then
    log "M6: OK (vérifié)"
    ssh "$M6_HOST" "ls -1t $M6_DIR/board_*.db.gz 2>/dev/null | tail -n +$((KEEP+1)) | xargs -r -I{} sh -c 'rm -f {} {}.sha256'"
  else
    log "M6: ÉCHEC copie/vérif"
  fi
else
  log "M6: injoignable, skip"
fi

# 3. → SSD M1 USB (disque fragile : sync + relecture sha256 obligatoires)
if [ -d "$(dirname "$USB_DIR")" ] && mkdir -p "$USB_DIR" 2>/dev/null; then
  if cp "$LOCAL_DIR/$GZ" "$LOCAL_DIR/$GZ.sha256" "$USB_DIR/" && sync \
     && (cd "$USB_DIR" && sha256sum -c "$GZ.sha256" >/dev/null); then
    log "SSD M1 USB: OK (vérifié)"
    rotate "$USB_DIR"
  else
    log "SSD M1 USB: ÉCHEC copie/vérif (disque fragile ?)"
  fi
else
  log "SSD M1 USB: non monté, skip"
fi

# 4. Rotation locale
rotate "$LOCAL_DIR"
log "terminé"
