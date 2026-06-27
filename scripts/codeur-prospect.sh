#!/bin/bash
# Prospection Codeur.com — scan missions + draft candidature auto
# Usage: bash codeur-prospect.sh [--post]

set -euo pipefail
LOG=/home/pamerys/jarvis/logs/codeur-$(date +%Y%m%d).log
BUFFER=/home/pamerys/jarvis/content_buffer/codeur_missions.json

log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

log "=== CODEUR.COM PROSPECTION ==="

# Vérifier si l'agent codeur est actif
CODEUR_AGENT="agent-codeur-agent-8466b5a3"
if openclaw agent status "$CODEUR_AGENT" &>/dev/null 2>&1; then
    log "Agent $CODEUR_AGENT actif"
    # Envoyer la tâche de scan
    openclaw agent run "$CODEUR_AGENT" \
      "Scanne codeur.com/freelances/missions pour Python/IA/Backend. Identifie les 5 meilleures missions. Pour chaque: titre, budget, délai, score_match (0-100). Retourne JSON." \
      --output "$BUFFER" &>/dev/null && log "✅ Scan lancé" || log "⚠ Agent unavailable"
else
    log "⚠ Agent codeur non actif — fallback lm-ask"
    bash ~/jarvis/scripts/lm-ask.sh \
      "Simule 5 missions Codeur.com Python/IA/Backend avec: titre, budget, délai, score_match. JSON array." \
      > "$BUFFER" 2>/dev/null
fi

log "Buffer: $BUFFER"
