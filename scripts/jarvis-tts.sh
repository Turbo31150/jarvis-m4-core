#!/usr/bin/env bash
# jarvis-tts.sh — hook Stop : vocalise la dernière réponse de Claude sur M4.
# Moteur : piper (offline, souverain) + voix fr_FR-siwis-medium.
# 100% fail-safe : ne bloque jamais la session, ne sort rien sur stdout.
set -u

# Kill-switch anti-boucle : touch ~/.cache/tts-off pour faire taire le vocal.
[ -f "$HOME/.cache/tts-off" ] && exit 0

TTS_LOG="$HOME/.cache/jarvis-tts.log"
PIPER="$HOME/.local/bin/piper"
VOICE="$HOME/jarvis/models/piper/fr_FR-siwis-medium.onnx"
MAXLEN=420

input=$(cat 2>/dev/null)
tpath=$(printf '%s' "$input" | jq -r '.transcript_path // empty' 2>/dev/null)
if [ -z "$tpath" ] || [ ! -f "$tpath" ]; then
  echo "$(date +%H:%M:%S) no transcript" >>"$TTS_LOG" 2>/dev/null; exit 0
fi

clean=$(python3 "$HOME/.claude/hooks/tts-prepare.py" "$tpath" "$MAXLEN" 2>/dev/null)
[ -z "$clean" ] && { echo "$(date +%H:%M:%S) empty" >>"$TTS_LOG" 2>/dev/null; exit 0; }

tmp="/tmp/jarvis-tts-$$.wav"
if printf '%s' "$clean" | "$PIPER" --model "$VOICE" --output_file "$tmp" >/dev/null 2>&1 && [ -s "$tmp" ]; then
  export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
  unset PULSE_SERVER
  # Anti-boucle STT : coupe le micro pendant la lecture, unmute garanti par trap.
  _mute(){ pactl set-source-mute @DEFAULT_SOURCE@ "$1" 2>/dev/null; }
  _mute 1; trap '_mute 0' EXIT
  if   command -v paplay >/dev/null 2>&1; then paplay "$tmp" >/dev/null 2>&1
  elif command -v pw-play >/dev/null 2>&1; then pw-play "$tmp" >/dev/null 2>&1
  elif command -v aplay  >/dev/null 2>&1; then aplay  "$tmp" >/dev/null 2>&1
  fi
  echo "$(date +%H:%M:%S) spoke ${#clean}c" >>"$TTS_LOG" 2>/dev/null
else
  echo "$(date +%H:%M:%S) piper fail" >>"$TTS_LOG" 2>/dev/null
fi
rm -f "$tmp"
exit 0
