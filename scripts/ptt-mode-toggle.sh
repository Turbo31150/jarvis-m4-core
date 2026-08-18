#!/usr/bin/env bash
# Bascule mode Alt+X : dictée <-> assistant
MODE_FILE="$HOME/.config/jarvis/ptt-mode"
mkdir -p "$(dirname "$MODE_FILE")"
[[ -f "$MODE_FILE" ]] || echo "dictée" > "$MODE_FILE"
CURRENT=$(<"$MODE_FILE")
if [[ "$CURRENT" == "dictée" || "$CURRENT" == "dictee" ]]; then
  echo "assistant" > "$MODE_FILE"
  notify-send -t 2500 -i emblem-synchronizing "JARVIS Mode" "🤖 ASSISTANT (qwen + voix Piper)"
else
  echo "dictée" > "$MODE_FILE"
  notify-send -t 2500 -i input-keyboard "JARVIS Mode" "⌨️ DICTÉE (corrige + écrit au curseur)"
fi
cat "$MODE_FILE"
