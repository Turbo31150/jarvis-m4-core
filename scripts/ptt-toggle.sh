#!/usr/bin/env bash
# JARVIS Push-to-Talk Alt+X
# Mode lu depuis ~/.config/jarvis/ptt-mode (dictée|assistant)
# - dictée   : Whisper -> qwen nettoie -> auto-type au curseur
# - assistant: Whisper -> qwen répond -> Piper TTS dans le casque
set -euo pipefail
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export PULSE_RUNTIME_PATH="$XDG_RUNTIME_DIR/pulse"
unset PULSE_SERVER || true

PID_FILE=/tmp/jarvis-ptt.pid
WAV_FILE=/tmp/jarvis-ptt.wav
LOG=/tmp/jarvis-ptt.log
HIST="$HOME/jarvis-voix.txt"
MODE_FILE="$HOME/.config/jarvis/ptt-mode"
WHISPER_URL="http://127.0.0.1:9743/v1/audio/transcriptions"
LLM_URL="http://127.0.0.1:1234/v1/chat/completions"
LLM_MODEL="qwen/qwen3.5-9b"
PIPER_BIN="$HOME/.local/bin/piper"
PIPER_VOICE="/home/pamerys/Workspaces/jarvis-linux/models/fr_FR-siwis-medium.onnx"
SOURCE="bluez_input.AC_80_0A_35_A1_4F.0"

mkdir -p "$(dirname "$MODE_FILE")"
[[ -f "$MODE_FILE" ]] || echo "dictée" > "$MODE_FILE"
MODE=$(<"$MODE_FILE")

log(){ echo "[$(date '+%H:%M:%S')] [$MODE] $*" >> "$LOG"; }

call_llm(){
  # $1=system $2=user → echo le content (vide si KO)
  local sys="$1" usr="$2"
  local req
  req=$(python3 -c "
import json,sys
print(json.dumps({
  'model':'$LLM_MODEL',
  'messages':[{'role':'system','content':sys.argv[1]},{'role':'user','content':sys.argv[2]}],
  'max_tokens':1500,'temperature':0.3
}))
" "$sys" "$usr")
  curl -sS --max-time 60 "$LLM_URL" -H "Content-Type: application/json" -d "$req" 2>>"$LOG" \
    | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    print(d['choices'][0]['message'].get('content','').strip())
except Exception:
    pass
" 2>>"$LOG"
}

# ----------- TOGGLE STOP -----------
if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  PID=$(cat "$PID_FILE")
  kill "$PID" 2>/dev/null || true
  sleep 0.2
  rm -f "$PID_FILE"
  notify-send -t 1500 -i microphone-sensitivity-muted "JARVIS [$MODE]" "🛑 Transcription..."

  if [[ ! -s "$WAV_FILE" ]]; then
    notify-send -u normal -t 3000 "JARVIS" "Audio vide"; exit 1
  fi

  # --- STT
  TXT=$(curl -sS --max-time 30 -F "file=@$WAV_FILE" -F "language=fr" "$WHISPER_URL" 2>>"$LOG" \
        | python3 -c "import sys,json;print(json.load(sys.stdin).get('text','').strip())" 2>>"$LOG")
  [[ -z "$TXT" ]] && { notify-send -u normal -t 4000 "JARVIS" "Aucune transcription"; exit 1; }
  log "STT: $TXT"
  printf '%s' "$TXT" | xclip -selection clipboard 2>/dev/null || true

  if [[ "$MODE" == "dictée" || "$MODE" == "dictee" ]]; then
    # --- Mode DICTÉE : qwen corrige le texte sans répondre
    CLEAN=$(call_llm \
      "Tu es un correcteur de transcription vocale française. On te donne le texte brut sorti d'un STT. Tu retournes UNIQUEMENT le même texte corrigé : ponctuation, majuscules, accents, fautes évidentes. Tu ne reformules pas, ne réponds pas, n'ajoutes rien. Pas de markdown, pas de guillemets, pas d'explication." \
      "$TXT")
    CLEAN=${CLEAN:-$TXT}
    log "CLEAN: $CLEAN"
    printf '[%s] [dictée] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$CLEAN" >> "$HIST"
    printf '%s' "$CLEAN" | xclip -selection clipboard 2>/dev/null || true
    (sleep 0.15; xdotool type --clearmodifiers --delay 6 -- "$CLEAN") &
    notify-send -t 4000 -i input-keyboard "JARVIS ✓ dictée" "$CLEAN"
    exit 0
  fi

  # --- Mode ASSISTANT : qwen répond, Piper parle
  notify-send -t 2500 -i emblem-synchronizing "🎙️ Toi" "$TXT"
  RESP=$(call_llm \
    "Tu es JARVIS, assistant vocal en français. Tu réponds en 1 à 3 phrases courtes, ton naturel et direct, sans markdown, sans emoji, sans liste. Tu vouvoies pas, tu tutoies." \
    "$TXT")
  RESP=${RESP:-"Désolé je n'ai pas de réponse."}
  log "LLM: $RESP"
  printf '[%s] [assist] Q: %s\n[%s] [assist] R: %s\n\n' \
    "$(date '+%Y-%m-%d %H:%M:%S')" "$TXT" "$(date '+%Y-%m-%d %H:%M:%S')" "$RESP" >> "$HIST"
  notify-send -t 6000 -i audio-volume-high "🤖 JARVIS" "$RESP"
  (printf '%s' "$RESP" | "$PIPER_BIN" --model "$PIPER_VOICE" --output_raw 2>>"$LOG" \
    | paplay --raw --rate=22050 --channels=1 --format=s16le 2>>"$LOG") &
  exit 0
fi

# ----------- TOGGLE START -----------
rm -f "$WAV_FILE"
log "START rec from $SOURCE"
# Essai 1 : bluetooth casque ; fallback : source par défaut
if pactl list short sources 2>/dev/null | grep -q "$SOURCE"; then
  parecord --device="$SOURCE" --rate=16000 --channels=1 --format=s16le "$WAV_FILE" >>"$LOG" 2>&1 &
elif command -v parecord >/dev/null && pactl info >/dev/null 2>&1; then
  parecord --rate=16000 --channels=1 --format=s16le "$WAV_FILE" >>"$LOG" 2>&1 &
else
  arecord -D pipewire -q -f S16_LE -r 16000 -c 1 "$WAV_FILE" >>"$LOG" 2>&1 &
fi
echo $! > "$PID_FILE"
notify-send -t 2000 -i audio-input-microphone "JARVIS [$MODE]" "🎙️ Enregistrement... (Alt+X = stop)"
