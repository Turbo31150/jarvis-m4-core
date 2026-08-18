#!/usr/bin/env bash
# Widget systray JARVIS PTT — yad notification
# Clic gauche = parler (Alt+X), Clic droit = menu (changer mode, historique, quitter)
set -u
MODE_FILE="$HOME/.config/jarvis/ptt-mode"
PID_FILE=/tmp/jarvis-ptt-widget.pid

mkdir -p "$(dirname "$MODE_FILE")"
[[ -f "$MODE_FILE" ]] || echo "dictée" > "$MODE_FILE"

# Si déjà actif → quitter proprement
if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  exit 0
fi
echo $$ > "$PID_FILE"
trap 'rm -f "$PID_FILE"' EXIT

icon_for(){
  case "$1" in
    dictée|dictee) echo "input-keyboard" ;;
    assistant)     echo "audio-headphones" ;;
    *)             echo "audio-input-microphone" ;;
  esac
}

# Process producer: monitor mode file et envoie commandes à yad sur stdout
{
  prev=""
  while :; do
    cur=$(<"$MODE_FILE" 2>/dev/null) || cur="dictée"
    if [[ "$cur" != "$prev" ]]; then
      echo "icon:$(icon_for "$cur")"
      echo "tooltip:JARVIS PTT — Mode: $cur   |   Alt+X = parler   |   Alt+Shift+X = changer mode"
      prev="$cur"
    fi
    sleep 1
  done
} | yad --notification --listen \
    --image="$(icon_for "$(<"$MODE_FILE")")" \
    --text="JARVIS PTT" \
    --command="bash /home/pamerys/jarvis/scripts/ptt-toggle.sh" \
    --menu="🎙 Parler (Alt+X)!bash /home/pamerys/jarvis/scripts/ptt-toggle.sh!audio-input-microphone|↔ Changer mode (Alt+Shift+X)!bash /home/pamerys/jarvis/scripts/ptt-mode-toggle.sh!view-refresh|📜 Historique!xdg-open $HOME/jarvis-voix.txt!text-x-generic|📊 Logs PTT!gnome-terminal -- bash -c 'tail -f /tmp/jarvis-ptt.log; read'!utilities-system-monitor|❌ Quitter!quit!process-stop"
