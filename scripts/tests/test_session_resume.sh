#!/usr/bin/env bash
set -uo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
source "$DIR/_assert.sh"
S="/home/pamerys/jarvis/scripts/session-resume.sh"

echo "TEST: reset court-circuite le garde-fou"
"$S" reset >/dev/null 2>&1; assert_exit 0 "$?" "reset exit 0"

echo "TEST: 3 reprises rapides → garde-fou STOP (exit 42)"
"$S" reset >/dev/null 2>&1
"$S" log >/dev/null 2>&1; r1=$?
"$S" log >/dev/null 2>&1; r2=$?
"$S" log >/dev/null 2>&1; r3=$?
assert_eq 0 "$r1" "run1 OK"
assert_eq 0 "$r2" "run2 OK"
assert_eq 42 "$r3" "run3 bloqué"

echo "TEST: stop pose le flag → reprise gelée"
"$S" reset >/dev/null 2>&1
"$S" stop  >/dev/null 2>&1
out="$("$S" auto 2>&1)"; assert_contains "$out" "gelée" "auto gelé après stop"
"$S" reset >/dev/null 2>&1

echo "TEST: axe snapshot calcule un âge plausible (<100000j)"
out="$("$S" snapshot 2>&1)"
age="$(printf '%s' "$out" | grep -oE 'il y a [0-9]+j' | grep -oE '[0-9]+' | head -1)"
plausible=$( { [ -n "$age" ] && [ "$age" -lt 100000 ]; } && echo true || echo false )
assert_eq true "$plausible" "âge snapshot plausible (<100000j) [âge=$age]"

report
