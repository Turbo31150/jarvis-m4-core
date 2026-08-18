#!/usr/bin/env bash
# Rappel quotidien des échéances prospection. RAPPELLE seulement, n'envoie rien.
LOG="$HOME/labo/bibliotheque/prospection/rappels.log"
OUT=$(bash "$HOME/labo/bibliotheque/series/prospect-planning.sh" due 2>/dev/null)
echo "=== $(date '+%Y-%m-%d %H:%M') ===" >> "$LOG"; echo "$OUT" >> "$LOG"
# notif bureau si une échéance est due (ligne commençant par "  [")
if echo "$OUT" | grep -q '^\s*\['; then
  command -v notify-send >/dev/null && DISPLAY=:0 notify-send "📅 Prospection — action due" "$(echo "$OUT" | grep '^\s*\[' | head -3)" 2>/dev/null
fi
