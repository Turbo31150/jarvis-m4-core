#!/usr/bin/env bash
# TTS local 0-token — piper (fr_FR-siwis-medium) → ALSA direct (contourne PipeWire cassé sur M4).
# Usage: speak.sh "texte à dire"   |   echo "texte" | speak.sh
set -euo pipefail

MODEL="${PIPER_MODEL:-$HOME/jarvis/models/piper/fr_FR-siwis-medium.onnx}"
ALSA_DEV="${SPEAK_ALSA_DEV:-plughw:CARD=PCH,DEV=0}"
TXT="${*:-$(cat)}"
WAV="$(mktemp --suffix=.wav)"
trap 'rm -f "$WAV"' EXIT

# Démutage de sécurité (carte 1 = PCH analogique)
amixer -c 1 sset 'Master'    100% unmute >/dev/null 2>&1 || true
amixer -c 1 sset 'Speaker'   100% unmute >/dev/null 2>&1 || true
amixer -c 1 sset 'Headphone' 100% unmute >/dev/null 2>&1 || true
amixer -c 1 sset 'Auto-Mute Mode' Disabled >/dev/null 2>&1 || true

printf '%s' "$TXT" | piper --model "$MODEL" --output_file "$WAV" 2>/dev/null
aplay -D "$ALSA_DEV" "$WAV" 2>/dev/null
