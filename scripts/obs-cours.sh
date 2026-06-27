#!/bin/bash
# OBS auto-record pour cours PAMERYS
# Usage: obs-cours.sh [start|stop|status]

SCENE="Cours"
OBS_WEBSOCKET="localhost:4455"
LOG="/home/pamerys/jarvis/logs/obs-cours.log"
RECORD_DIR="/home/pamerys/Videos/Cours"

mkdir -p "$RECORD_DIR"

case "${1:-start}" in
  start)
    echo "$(date): Démarrage enregistrement cours..." >> "$LOG"
    # Lance OBS en mode minimisé si pas déjà lancé
    if ! pgrep -x obs > /dev/null; then
        obs --minimize-to-tray &
        sleep 3
    fi
    # Active la scène "Cours" et démarre l'enregistrement
    # via obs-cmd si disponible, sinon via xdotool
    if command -v obs-cmd &>/dev/null; then
        obs-cmd --websocket obswebsocket://localhost:4455 recording start 2>/dev/null
    else
        notify-send "JARVIS OBS" "Enregistrement cours démarré" --icon=video-x-generic
    fi
    echo "$(date): OBS lancé" >> "$LOG"
    ;;
  stop)
    echo "$(date): Arrêt enregistrement..." >> "$LOG"
    if command -v obs-cmd &>/dev/null; then
        obs-cmd --websocket obswebsocket://localhost:4455 recording stop 2>/dev/null
    fi
    notify-send "JARVIS OBS" "Enregistrement terminé → $RECORD_DIR" --icon=video-x-generic
    echo "$(date): Arrêt OK" >> "$LOG"
    ;;
  status)
    if pgrep -x obs > /dev/null; then
        echo "OBS: RUNNING"
    else
        echo "OBS: STOPPED"
    fi
    ;;
esac
