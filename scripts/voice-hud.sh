#!/usr/bin/env bash
# Launcher JARVIS Voice HUD — singleton, log dans ~/jarvis/voice_logs/hud.log
set -e
PID_FILE="/tmp/jarvis_voice_hud.pid"
LOG="$HOME/jarvis/voice_logs/hud.log"
mkdir -p "$(dirname "$LOG")"

if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "VoiceHUD déjà actif PID=$(cat "$PID_FILE")"
  exit 0
fi

cd "$(dirname "$0")"
nohup python3 jarvis_voice_hud.py >> "$LOG" 2>&1 &
echo $! > "$PID_FILE"
echo "VoiceHUD lancé PID=$(cat "$PID_FILE")"
