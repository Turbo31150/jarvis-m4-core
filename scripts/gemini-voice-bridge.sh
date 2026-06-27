#!/bin/bash
# gemini-voice-bridge.sh — Pont Lumen/WhisperFlow → gemini-smart.sh
# Utilisé quand l'entrée vient du pipeline vocal (STT → Gemini → TTS)
#
# Usage:
#   echo "texte transcrit" | gemini-voice-bridge.sh [--source lumen|whisperflow]
#   gemini-voice-bridge.sh --source whisperflow "question vocale"
#
# Output JSON pour le pipeline vocal :
#   {"output":"réponse","status":"ok","model":"...","dur_s":1.2}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="lumen"

while [[ "${1:-}" == --* ]]; do
  case "$1" in
    --source) SOURCE="$2"; shift 2 ;;
    *) shift ;;
  esac
done

PROMPT="${*:-}"
[[ -t 0 ]] || PROMPT="$(cat)${PROMPT:+ }${PROMPT}"
PROMPT="${PROMPT# }"

[[ -z "$PROMPT" ]] && exit 1

# Pipeline vocal = toujours tâches courtes + réponse rapide
# Flash : moins de latence, moins de blocage thinking
# JSON output pour parsing par Lumen/WhisperFlow
exec bash "$SCRIPT_DIR/gemini-smart.sh" \
  --short \
  --via "$SOURCE" \
  --json \
  --no-fallback \
  "$PROMPT"
