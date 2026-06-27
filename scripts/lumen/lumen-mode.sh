#!/usr/bin/env bash
# Raccourci: switcher le mode de traitement Lumen
# Usage: lumen-mode.sh [auto|classroom|translation|document|research|meeting|speed|balanced|deep|consensus]
LUMEN_API="http://127.0.0.1:8788/api/control"
MODE="${1:-auto}"

# Déterminer si c'est un taskMode ou un orchestrationProfile
case "$MODE" in
  auto|classroom|translation|document|research|meeting)
    PAYLOAD="{\"taskMode\":\"$MODE\"}"
    LABEL="Task: $MODE"
    ;;
  speed|balanced|deep|consensus)
    PAYLOAD="{\"orchestrationProfile\":\"$MODE\"}"
    LABEL="Profil: $MODE"
    ;;
  whisper|jarvis-whisper)
    PAYLOAD="{\"transcriptionMode\":\"jarvis-whisper\"}"
    LABEL="STT: Whisper JARVIS"
    ;;
  gemini|gemini-live)
    PAYLOAD="{\"transcriptionMode\":\"gemini-live\"}"
    LABEL="STT: Gemini Live"
    ;;
  browser|browser-local)
    PAYLOAD="{\"transcriptionMode\":\"browser-local\"}"
    LABEL="STT: Browser local"
    ;;
  detect)
    curl -sf "${LUMEN_API}/detect-mode" > /tmp/lumen-mode.json 2>/dev/null
    DETECTED=$(python3 -c "import json; d=json.load(open('/tmp/lumen-mode.json')); print(d.get('mode','?'))" 2>/dev/null)
    notify-send -t 2000 -i system-run "Lumen Auto-Detect" "Mode détecté: $DETECTED"
    exit 0
    ;;
  *)
    notify-send -t 2000 -i dialog-error "Lumen" "Mode inconnu: $MODE"
    exit 1
    ;;
esac

curl -sf -X POST "${LUMEN_API}/mode" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" > /dev/null 2>&1

notify-send -t 1500 -i preferences-system "Lumen" "$LABEL"
