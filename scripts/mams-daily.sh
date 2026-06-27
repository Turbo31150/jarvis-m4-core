#!/bin/bash
# JARVIS MAMS Daily — question aléatoire au démarrage
JARVIS=/home/pamerys/jarvis

# Sélection question aléatoire depuis JSON
Q=$(python3 -c "
import json, random, pathlib
f = pathlib.Path('$JARVIS/multiagent/mams_questions_jury.json')
if f.exists():
    qs = json.loads(f.read_text())
    q = random.choice(qs)
    print(f\"[{q['theme']}] {q['q']}\")
else:
    print('Prépare-toi pour MAMS le 2 juin!')
")

# Notification GNOME
DISPLAY=:0 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
  notify-send "🎯 JARVIS MAMS du jour" "$Q" --icon=dialog-question --expire-time=10000 2>/dev/null || true

# Log
echo "$(date +%Y-%m-%d) — $Q" >> $JARVIS/logs/mams-daily.log

# Affichage terminal si lancé depuis terminal
if [ -t 1 ]; then
    echo ""
    echo "╔══════════════════════════════════════╗"
    echo "║  🎯 QUESTION MAMS DU JOUR            ║"
    echo "╚══════════════════════════════════════╝"
    echo "$Q"
    echo ""
fi
