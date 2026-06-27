#!/bin/bash
# JARVIS Voice Widget launcher — singleton (1 seule instance)
PIDFILE="/tmp/voice_widget.pid"

# Si déjà en cours → envoyer SIGUSR1 pour toggle enregistrement
if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if kill -0 "$PID" 2>/dev/null; then
        # Widget déjà actif : toggle via SIGUSR1
        kill -USR1 "$PID"
        exit 0
    fi
    rm -f "$PIDFILE"
fi

# Lancer nouvelle instance
export PYTHONPATH="/home/pamerys/Workspaces/jarvis-linux:/home/pamerys/Workspaces/jarvis-linux/src"
python3 /home/pamerys/jarvis/scripts/voice_widget.py "$@" &
echo $! > "$PIDFILE"
