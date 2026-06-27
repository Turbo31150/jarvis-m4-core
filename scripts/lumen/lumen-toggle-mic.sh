#!/usr/bin/env bash
# Raccourci: toggle micro Lumen + détection auto du mode selon app active
LUMEN_API="http://127.0.0.1:8788/api/control"

# Détecter mode auto avant toggle
curl -sf "${LUMEN_API}/detect-mode" > /dev/null 2>&1

# Toggle micro
STATE=$(curl -sf -X POST "${LUMEN_API}/mic" \
  -H "Content-Type: application/json" \
  -d '{"action":"toggle"}' 2>/dev/null)

MIC=$(echo "$STATE" | python3 -c "import sys,json; d=json.load(sys.stdin); print('ON' if d.get('micActive') else 'OFF')" 2>/dev/null || echo "?")

# Notification visuelle
notify-send -t 2000 -i audio-input-microphone \
  "Lumen Micro $MIC" \
  "$(curl -sf "${LUMEN_API}/status" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"Mode: {d.get('taskMode','?')} | {d.get('transcriptionMode','?')}\")" 2>/dev/null)"

# Ouvrir Lumen si micro ON et pas déjà ouvert
if [ "$MIC" = "ON" ]; then
  pgrep -f "lumen\|4173\|8788" > /dev/null || xdg-open http://127.0.0.1:4173 &
fi
