#!/bin/bash
# Démarrage rapide - Mode Enseignante JARVIS M4
# Lance les outils essentiels au début de la journée

export DISPLAY=:0
export XAUTHORITY=/home/pamerys/.Xauthority
export XDG_RUNTIME_DIR=/run/user/1000
export PULSE_SERVER=unix:/run/user/1000/pulse/native

echo "🎓 Démarrage Mode Enseignante..."

# 1. Vérifier/démarrer JARVIS Voice Widget
if ! pgrep -f voice_widget.py > /dev/null; then
    nohup python3 ~/jarvis/scripts/voice_widget.py > ~/jarvis/logs/voice_widget.log 2>&1 &
    echo "✅ Widget vocal démarré (Alt+X pour dicter)"
else
    echo "✅ Widget vocal déjà actif"
fi

# 2. Notification bureau
notify-send "🎓 JARVIS Enseignante" "Système prêt\nAlt+X pour dicter\nFlameshot pour captures" --icon=audio-input-microphone -t 5000 2>/dev/null || true

echo "Tout est prêt !"
