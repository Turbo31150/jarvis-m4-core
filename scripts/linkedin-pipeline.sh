#!/usr/bin/env bash
# linkedin-pipeline — chaîne 0-token : garde-fou chiffres → table ronde → verdict → journal.
#
#   linkedin-pipeline sonde              qui répond réellement (délègue à jarvis-table-ronde)
#   linkedin-pipeline garde <fichier>    refuse les chiffres périmés (LOI 3). Code 1 si violation.
#   linkedin-pipeline valide <fichier>   garde + débat board/hub/m6 + verdict + journal
#   linkedin-pipeline journal            10 derniers passages
#
# Aucun appel cloud facturé : sièges board/hub/m6 (LOI 2).
set -uo pipefail

TR="$HOME/.local/bin/jarvis-table-ronde"
LOGDB="$HOME/jarvis/logs/jarvis_logs.db"
TRACES="$HOME/jarvis/data/tables-rondes"

# Chiffres retirés le 18/08/2026 (kit_dispatch_jarvis.md). Les laisser passer,
# c'est publier une affirmation qu'aucune mesure ne soutient.
INTERDITS='12 GPU|6 machines|1000\+|< ?300 ?ms|<300ms'

_journal() {  # phase, cible, verdict, detail
  mkdir -p "$(dirname "$LOGDB")"
  sqlite3 "$LOGDB" "CREATE TABLE IF NOT EXISTS linkedin_pipeline(
      id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, phase TEXT,
      cible TEXT, verdict TEXT, detail TEXT);
    INSERT INTO linkedin_pipeline(ts,phase,cible,verdict,detail)
    VALUES(datetime('now'),'$1','$2','$3','$(printf '%s' "${4:-}" | sed "s/'/''/g" | tr '\n' ' ')');" 
}

garde() {
  local f="${1:?fichier requis}"
  [ -f "$f" ] || { echo "✗ introuvable : $f"; exit 2; }
  # On ignore la ligne de contrôle qui LISTE les interdits sans les affirmer.
  local hits
  hits=$(grep -n -E "$INTERDITS" "$f" | grep -v -i 'INTERDITS' || true)
  if [ -n "$hits" ]; then
    echo "⛔ GARDE-FOU — chiffres périmés dans $f :"
    echo "$hits" | sed 's/^/   /'
    echo "   Autorisés : 5 GPU sur 2 machines · 319 agents indexés · 272 464 chunks FTS5 (mesuré 19/08)."
    _journal garde "$f" REFUS "$hits"
    return 1
  fi
  echo "✓ garde-fou : aucun chiffre périmé dans $(basename "$f")"
  _journal garde "$f" OK ""
  return 0
}

valide() {
  local f="${1:?fichier requis}"
  garde "$f" || { echo "→ débat non lancé : corrige les chiffres d'abord."; exit 1; }
  local sujet
  sujet="Valide ou refuse ce contenu LinkedIn destiné à des dirigeants de PME françaises.
Juge trois choses seulement : (1) est-ce crédible face à un technicien, (2) est-ce que
ça donne envie de répondre, (3) qu'est-ce qui sonne faux ou creux. Sois direct et bref.
--- CONTENU ---
$(cat "$f")"
  echo "── Table ronde 0-token (sièges : ${TABLE_RONDE_SIEGES:-board hub m6}) ──"
  local out
  out=$("$TR" debat "$sujet" 2>&1)
  echo "$out"
  local trace
  trace=$(printf '%s' "$out" | sed -n 's/^Trace : //p' | tail -1)
  _journal debat "$f" RENDU "${trace:-sans trace}"
  echo
  echo "→ Journal : sqlite3 $LOGDB \"SELECT * FROM linkedin_pipeline ORDER BY id DESC LIMIT 5;\""
}

journal() {
  sqlite3 -header -column "$LOGDB" \
    "SELECT id,ts,phase,verdict,substr(detail,1,50) AS detail FROM linkedin_pipeline
     ORDER BY id DESC LIMIT 10;" 2>/dev/null || echo "(journal vide)"
}

case "${1:-}" in
  sonde)   shift; "$TR" sonde "$@" ;;
  garde)   shift; garde "$@" ;;
  valide)  shift; valide "$@" ;;
  journal) journal ;;
  *) sed -n '2,12p' "$0" ;;
esac
