#!/usr/bin/env bash
set -uo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
source "$DIR/_assert.sh"
H="/home/pamerys/jarvis/scripts/session-handoff.sh"

# Sandbox isolé pour ne pas écraser le vrai .remember
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
printf '## 10:00 | test\nLigne buffer A\n## 10:05 | test\nLigne buffer B\n' > "$TMP/now.md"

echo "TEST: génère un remember.md non vide à partir de now.md"
REMEMBER_DIR="$TMP" "$H" >/dev/null 2>&1; ec=$?
assert_exit 0 "$ec" "handoff exit 0"
nonempty=$( [ -s "$TMP/remember.md" ] && echo true || echo false )
assert_eq true "$nonempty" "remember.md non vide"

echo "TEST: le handoff contient la dernière ligne du buffer"
content="$(cat "$TMP/remember.md" 2>/dev/null)"
assert_contains "$content" "Ligne buffer B" "dernière entrée présente"

echo "TEST: le handoff contient un horodatage"
assert_contains "$content" "HANDOFF" "en-tête HANDOFF présent"

report
