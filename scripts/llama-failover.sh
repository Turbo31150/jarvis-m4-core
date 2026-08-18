#!/bin/bash
LLAMA_PORT=8080
LMS_PORT=1234
CHECK_INTERVAL=20
LMS_ACTIVE=false

log() { echo "[$(date '+%H:%M:%S')] $1"; }

while true; do
    if curl -sf --max-time 5 http://localhost:$LLAMA_PORT/health > /dev/null 2>&1; then
        if [ "$LMS_ACTIVE" = true ]; then
            log '✅ llama-server back — LM Studio reste disponible'
            LMS_ACTIVE=false
        fi
    else
        if [ "$LMS_ACTIVE" = false ]; then
            log '⚠️  llama-server KO — LM Studio :1234 prend le relais'
            # Notifier OpenClaw via M1
            curl -sf --max-time 3 http://192.168.1.85:18789/api/notify               -d '{"event":"llama_down","fallback":"lmstudio:1234"}' 2>/dev/null
            LMS_ACTIVE=true
        fi
        log '🔄 Fallback actif → LM Studio :'""
    fi
    sleep $CHECK_INTERVAL
done
