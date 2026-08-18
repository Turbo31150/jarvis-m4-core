#!/bin/bash
# Triage Gmail automatique via script Python natif
set -euo pipefail
LOG=/home/pamerys/jarvis/logs/mail-$(date +%Y%m%d).log

log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }
log "=== MAIL TRIAGE INTENSIF NAF ==="

python3 /home/pamerys/jarvis/scripts/mail_sorter_organizer.py >> "$LOG" 2>&1 && log "✅ Triage & Rangement Intensif OK" || log "⚠ Erreur Triage"
