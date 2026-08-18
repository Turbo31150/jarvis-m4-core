#!/bin/bash
# JARVIS Voice Widget launcher
export PYTHONPATH="/home/pamerys/Workspaces/jarvis-linux:/home/pamerys/Workspaces/jarvis-linux/src"

# Session Wayland : le cookie Xwayland de mutter est enregistré sans numéro de
# display ("hote/unix:"), ce que python-xlib (pynput) refuse. On recopie le
# cookie dans ~/.Xauthority avec un display explicite ":0".
# VERROU SINGLETON — le 2026-08-18 ce widget s'est multiplié en 189 instances
# (charge moyenne 285, CPU à 95 °C) parce qu'il crashait au démarrage et était
# relancé sans fin. Un seul exemplaire peut désormais tourner : les suivants
# sortent immédiatement au lieu de s'empiler.
exec 9>"/run/user/$(id -u)/jarvis-voice-widget.lock"
if ! flock -n 9; then
    echo "voice_widget : une instance tourne deja — abandon." >&2
    exit 0
fi

# ÉCRAN : ne PAS coder ":0" en dur. L'affichage réel de cette session est ":1" ;
# forcer ":0" faisait échouer tk.Tk() à chaque lancement. On retient le premier
# display qui accepte réellement une connexion.
if [ -z "${DISPLAY:-}" ] || ! timeout 3 xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then
    for d in :1 :0 :2; do
        if timeout 3 xdpyinfo -display "$d" >/dev/null 2>&1; then
            export DISPLAY="$d"; break
        fi
    done
fi
export DISPLAY="${DISPLAY:-:1}"
echo "voice_widget : DISPLAY retenu = $DISPLAY" >&2
if [ -n "$WAYLAND_DISPLAY" ] || ls /run/user/$(id -u)/.mutter-Xwaylandauth.* >/dev/null 2>&1; then
    MUTTER_XAUTH=$(ls -t /run/user/$(id -u)/.mutter-Xwaylandauth.* 2>/dev/null | head -1)
    if [ -n "$MUTTER_XAUTH" ]; then
        COOKIE=$(xauth -f "$MUTTER_XAUTH" list 2>/dev/null | head -1 | awk '{print $3}')
        if [ -n "$COOKIE" ]; then
            export XAUTHORITY="$HOME/.Xauthority"
            touch "$XAUTHORITY"
            xauth -f "$XAUTHORITY" add "$DISPLAY" MIT-MAGIC-COOKIE-1 "$COOKIE" 2>/dev/null
        fi
    fi
fi

exec python3 /home/pamerys/jarvis/scripts/voice_widget.py "$@"
