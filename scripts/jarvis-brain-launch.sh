#!/usr/bin/env bash
# Launcher idempotent (clic icône → toggle widget)
PIDFILE=/tmp/jarvis-brain.pid
if [[ -f "$PIDFILE" ]] && kill -0 "$(cat $PIDFILE)" 2>/dev/null; then
  kill "$(cat $PIDFILE)"; rm -f "$PIDFILE"; exit 0
fi
nohup /usr/bin/python3 "$HOME/jarvis/scripts/jarvis_voice_hud.py" >/tmp/jarvis-brain.log 2>&1 &
echo $! > "$PIDFILE"
