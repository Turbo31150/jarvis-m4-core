#!/bin/bash
# Triage Gmail automatique via agent mail
set -euo pipefail
LOG=/home/pamerys/jarvis/logs/mail-$(date +%Y%m%d).log
MAIL_AGENT="agent-mail-agent-f02809a3"

log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }
log "=== MAIL TRIAGE ==="

openclaw agent run "$MAIL_AGENT" \
  "Analyse inbox Gmail. Classe par priorité (URGENT/NORMAL/ARCHIVE). Draft réponses urgentes. Extrait TODO. Rapport JSON avec: total, urgent_count, todo_items, draft_count." \
  2>/dev/null | tee -a "$LOG" && log "✅ Triage OK" || log "⚠ Agent unavailable"
