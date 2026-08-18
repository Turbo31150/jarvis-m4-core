#!/usr/bin/env bash
# session-handoff.sh — Écrit le handoff de reprise (remember.md)
# depuis le buffer now.md + journal du jour. Idempotent. Zéro API.
set -uo pipefail
REM="${REMEMBER_DIR:-/home/pamerys/.remember}"
NOW="$REM/now.md"
TODAY="$REM/today-$(date +%F).md"
OUT="$REM/remember.md"
STAMP="$(date '+%F %H:%M')"

mkdir -p "$REM" || { echo "❌ Impossible de créer $REM" >&2; exit 1; }
{
  echo "=== HANDOFF $STAMP ==="
  echo "# Reprise : lire ce fichier puis lancer session-resume.sh auto"
  echo
  echo "## Dernières actions (buffer now.md)"
  if [ -s "$NOW" ]; then tail -20 "$NOW"; else echo "(buffer vide)"; fi
  echo
  if [ -s "$TODAY" ]; then
    echo "## Journal du jour (extrait)"
    tail -10 "$TODAY"
  fi
} > "$OUT" || { echo "❌ Échec écriture $OUT" >&2; exit 1; }
echo "✅ Handoff écrit : $OUT ($(wc -l < "$OUT" | tr -d ' ') lignes)"
