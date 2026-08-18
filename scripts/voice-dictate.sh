#!/bin/bash
# JARVIS Voice Dictation — Alt+X toggle (safe v3 avec debounce)

LOCK=/tmp/jarvis-dict.lock
WAV=/tmp/jarvis-dict.wav
LOG=/tmp/jarvis-dict.log
LASTCALL=/tmp/jarvis-dict.last
WHISPER=http://localhost:9743/v1/audio/transcriptions
MAX_SEC=30
DEBOUNCE_MS=800

exec >>"$LOG" 2>&1

# === DEBOUNCE: ignore rebounds < 800ms ===
NOW=$(date +%s%3N)
if [ -f "$LASTCALL" ]; then
    LAST=$(cat "$LASTCALL")
    DIFF=$((NOW - LAST))
    if [ $DIFF -lt $DEBOUNCE_MS ]; then
        echo "[$(date +%H:%M:%S.%3N)] DEBOUNCE skip (${DIFF}ms)"
        exit 0
    fi
fi
echo "$NOW" > "$LASTCALL"
echo "[$(date +%H:%M:%S.%3N)] ACCEPT, lock=$([ -f $LOCK ] && echo yes || echo no)"

# === TOGGLE OFF ===
if [ -f "$LOCK" ]; then
    PID=$(cat "$LOCK")
    kill "$PID" 2>/dev/null
    sleep 0.3  # laisse arecord flush le WAV proprement
    rm -f "$LOCK"
    notify-send -t 1200 "JARVIS" "🛑 Transcription…" 2>/dev/null

    SIZE=$(stat -c%s "$WAV" 2>/dev/null || echo 0)
    echo "[stop] wav size=$SIZE bytes"
    if [ ! -f "$WAV" ] || [ "$SIZE" -lt 8192 ]; then
        notify-send -t 2500 "JARVIS ⚠" "Enregistrement vide ou trop court ($SIZE B)" 2>/dev/null
        exit 0
    fi

    RESP=$(curl -s -m 30 "$WHISPER" \
        -F "file=@${WAV}" \
        -F "model=whisper-1" \
        -F "language=fr" 2>/dev/null)
    echo "[stop] whisper resp: ${RESP:0:200}"

    TXT=$(echo "$RESP" | jq -r '.text // empty' 2>/dev/null | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    if [ -z "$TXT" ]; then
        ERR=$(echo "$RESP" | jq -r '.error // "vide"' 2>/dev/null)
        notify-send -t 2500 "JARVIS ⚠" "Pas de texte (${ERR:0:60})" 2>/dev/null
        exit 0
    fi

    TXT=$(echo "$TXT" | sed -E 's/[[:space:],.!?]*[Tt]ermin[eé]r?[[:space:].!?]*$//')
    [ -z "$TXT" ] && exit 0

    sleep 0.2
    xdotool type --clearmodifiers --delay 8 -- "$TXT"
    notify-send -t 1800 "JARVIS ✓" "$(echo "$TXT" | head -c 80)" 2>/dev/null
    exit 0
fi

# === TOGGLE ON ===
notify-send -t 1500 "JARVIS" "🎙 Enregistrement (Alt+X stop, ${MAX_SEC}s max)" 2>/dev/null
rm -f "$WAV"
setsid arecord -D pipewire -q -f S16_LE -r 16000 -c 1 -d $MAX_SEC "$WAV" </dev/null >/dev/null 2>&1 &
APID=$!
echo "$APID" > "$LOCK"
echo "[start] arecord PID=$APID"
disown 2>/dev/null
exit 0
