#!/usr/bin/env bash
# jarvis-history-capture — CLI : capture l'historique navigateur → HTML + séries rejouables.
# But « plus besoin de navigateur » : lit les bases History (SQLite ro), aspire par curl
# (0 navigateur), génère blocs + séries replay rangés dans la bibliothèque. 0-token.
#
# Usage :
#   jarvis-history-capture all            # extract + series + résumé  (recommandé)
#   jarvis-history-capture extract        # (ré)indexe toutes les bases History
#   jarvis-history-capture series         # (re)génère blocs + séries replay
#   jarvis-history-capture aspire [N]     # télécharge le HTML de N pages (curl)
#   jarvis-history-capture top [N]        # top N domaines utiles (hors bruit auth)
#   jarvis-history-capture find <mot>     # cherche une URL/titre dans l'historique
#   jarvis-history-capture replay <dom>   # rejoue la capture d'un domaine (sans navigateur)
#   jarvis-history-capture hist           # état des captures
set -uo pipefail

SERIE="$HOME/labo/bibliotheque/series/history-capture.sh"
OUT="$HOME/jarvis/data/history-capture"
URLS_TSV="$OUT/urls.tsv"
REPLAY_DIR="$HOME/labo/bibliotheque/series/replay"
# domaines "bruit" (login/redirect/analytics) exclus des tops
NOISE='accounts.google.com|gstatic|doubleclick|googlesyndication|google-analytics|/sorry/|recaptcha'

[ -f "$SERIE" ] || { echo "✗ série manquante : $SERIE"; exit 1; }

OP="${1:-all}"; shift 2>/dev/null || true
case "$OP" in
  all|extract|series|hist|historique)
    bash "$SERIE" "$OP" "$@" ;;
  aspire)
    bash "$SERIE" aspire "${1:-50}" ;;
  top)
    N="${1:-25}"
    [ -f "$URLS_TSV" ] || bash "$SERIE" extract >/dev/null
    echo "▶ Top $N domaines utiles (hors login/analytics) :"
    awk -F'\t' 'NR>1{d=$4; sub(/^[a-z]+:\/\//,"",d); sub(/\/.*/,"",d); if(d!="")print d}' "$URLS_TSV" \
      | grep -vE "$NOISE" | sort | uniq -c | sort -rn | head -"$N" \
      | awk '{printf "  %5d  %s\n",$1,$2}' ;;
  find)
    mot="${1:?mot-clé requis}"
    [ -f "$URLS_TSV" ] || bash "$SERIE" extract >/dev/null
    echo "▶ URLs correspondant à « $mot » (index historique) :"
    grep -i -- "$mot" "$URLS_TSV" | awk -F'\t' '{printf "  %s  %s\n  ↳ %s\n",$1,$5,$4}' | head -40 ;;
  search)
    bash "$SERIE" search "${1:?mot-clé requis}" ;;
  replay)
    dom="${1:?domaine requis (voir: jarvis-history-capture top)}"
    f="$REPLAY_DIR/replay-$dom.sh"
    [ -f "$f" ] || { echo "✗ pas de série pour $dom. Lance d'abord : jarvis-history-capture series"; exit 1; }
    echo "▶ replay $dom (capture HTML, 0 navigateur)…"; bash "$f" ;;
  help|-h|--help)
    sed -n '2,20p' "$0" ;;
  *)
    bash "$SERIE" "$OP" "$@" ;;
esac
