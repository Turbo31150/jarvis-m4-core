#!/usr/bin/env bash
# Raccourci: injecter le dernier texte transcrit à la position du curseur
LUMEN_API="http://127.0.0.1:8788/api/control"

RESULT=$(curl -sf -X POST "${LUMEN_API}/inject" \
  -H "Content-Type: application/json" \
  -d '{"useLast":true}' 2>/dev/null)

OK=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('ok','false'))" 2>/dev/null || echo "false")
TEXT=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('injected','')[:60])" 2>/dev/null || echo "")

if [ "$OK" = "True" ] || [ "$OK" = "true" ]; then
  notify-send -t 1500 -i edit-paste "Lumen → Curseur" "$TEXT"
else
  REASON=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('reason', d.get('error','')))" 2>/dev/null || echo "")
  notify-send -t 2000 -i dialog-warning "Lumen" "Aucun texte à injecter ($REASON)"
fi
