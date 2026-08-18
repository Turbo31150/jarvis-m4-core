#!/usr/bin/env bash
# Moisson de recherche : chaque question part dans agy (Antigravity CLI), qui
# fait la recherche web et répond. Sortie = un fichier markdown par question,
# plus un rapport consolidé. 0 token Anthropic.
set -uo pipefail

QUESTIONS="${1:-$HOME/jarvis/data/questions-claude-code.txt}"
OUT="${2:-$HOME/jarvis/data/moisson-claude-code}"
EFFORT="${AGY_EFFORT:-medium}"
TIMEOUT="${AGY_TIMEOUT:-420}"

mkdir -p "$OUT"
n=0
while IFS= read -r q; do
  [ -z "$q" ] && continue
  n=$((n + 1))
  f=$(printf '%s/q%02d.md' "$OUT" "$n")
  # Idempotent : une question déjà répondue n'est pas repayée en temps machine.
  if [ -s "$f" ]; then
    echo "[$n] déjà fait — $f"
    continue
  fi
  echo "[$n] $q"
  {
    echo "## Q$n — $q"
    echo
    timeout "$TIMEOUT" agy -p "Recherche sur le web (sources récentes, 2026) et réponds de façon dense et actionnable, en français. Cite tes sources en fin de réponse. Question : $q" \
      --effort "$EFFORT" 2>&1 || echo "_(échec ou timeout après ${TIMEOUT}s)_"
    echo
  } >"$f"
done <"$QUESTIONS"

# Rapport consolidé
REPORT="$OUT/RAPPORT.md"
{
  echo "# Moisson — améliorer Claude Code"
  echo
  echo "Source : Antigravity CLI (\`agy\`, recherche web). $n questions."
  echo
  for f in "$OUT"/q*.md; do
    [ -s "$f" ] && cat "$f" && echo "---"
  done
} >"$REPORT"

echo "OK — $n questions · rapport : $REPORT"
