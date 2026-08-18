#!/usr/bin/env bash
# demo-weekly.sh — régénère la démo vidéo commerciale du widget planning (hebdo).
# 0-token : narration edge-tts + défilement JavaScript + capture ffmpeg (voir
# bin/demo-widget-scroll-js.py). Sortie : ~/jarvis/demo/widget-bureau.mp4
set -u

export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/gdm/Xauthority}"
[ -f "$XAUTHORITY" ] || export XAUTHORITY="$HOME/.Xauthority"

DEMO_DIR="$HOME/jarvis/demo"
LOG="$DEMO_DIR/demo-weekly.log"
GEN="$HOME/jarvis/planning-app/bin/demo-widget-scroll-js.py"
mkdir -p "$DEMO_DIR"

echo "=== $(date '+%F %T') — régénération démo ===" >>"$LOG"

# Le générateur a seulement besoin du backend HTTP :8899 (il crée sa propre
# fenêtre WebKit). On s'assure qu'il tourne, sinon on le démarre.
if ! curl -s -m5 http://127.0.0.1:8899/data >/dev/null 2>&1; then
    echo "widget :8899 absent → démarrage du service" >>"$LOG"
    systemctl --user start jarvis-planning-widget.service 2>>"$LOG"
    for _ in $(seq 1 12); do
        curl -s -m3 http://127.0.0.1:8899/data >/dev/null 2>&1 && break
        sleep 2
    done
fi

if ! command -v edge-tts >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/edge-tts" ]; then
    echo "ERREUR : edge-tts absent (pip install --user edge-tts)" >>"$LOG"
    exit 1
fi
export PATH="$HOME/.local/bin:$PATH"

python3 "$GEN" >>"$LOG" 2>&1
rc=$?
echo "=== fin $(date '+%F %T') (rc=$rc) → $DEMO_DIR/widget-bureau.mp4 ===" >>"$LOG"
exit $rc
