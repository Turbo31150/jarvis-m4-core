#!/usr/bin/env bash
# Synchronisation directe ultra-rapide M1/M6 (10.42.0.230 ASIX USB-C) -> SSD Local /data/m1-direct-sync/
set -u
DEST="/data/m1-direct-sync"
mkdir -p "$DEST"
LOG="$DEST/sync_all.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Début synchronisation M1 direct (10.42.0.230)..." | tee -a "$LOG"

DIRS=("prompts" "Workspaces" "scripts" "moisson_remi" "RESTORE_BACKUP_2026-08-09" "RECOVERY-M1" "sql-backups" ".openclaw" ".remember" "IA")

for d in "${DIRS[@]}"; do
  echo "[$(date '+%H:%M:%S')] Syncing $d..." | tee -a "$LOG"
  rsync -avz --partial \
    --exclude='*.iso' \
    --exclude='node_modules' \
    --exclude='.cache' \
    --exclude='*.tmp' \
    -e "ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no" \
    turbo@10.42.0.230:"/home/turbo/$d" "$DEST/" >> "$LOG" 2>&1 || true
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Synchronisation M1 terminée avec succès." | tee -a "$LOG"
