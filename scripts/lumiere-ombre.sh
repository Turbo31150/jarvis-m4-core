#!/bin/bash
# lumiere-ombre.sh — Primitive générique de boucle Lumière/Ombre.
#
#   LUMIÈRE = une action est exécutée (visible : demande → résultat)
#   OMBRE   = elle est journalisée + scorée (caché : log, durée, statut)
#   FEEDBACK= l'Ombre relue oriente la prochaine Lumière
#   BOUCLE  = feedback → action suivante mieux routée → re-log → …
#
# Réutilisable par n'importe quel script :
#   source lumiere-ombre.sh
#   out=$(lo_run "nom_action" ma_commande arg1 arg2)     # exécute + journalise
#   lo_feedback "nom_action"                              # taux d'échec / durée récents
#   lo_should_skip "nom_action" 30                        # 0 si KO récent (<30min) → sauter
#
# En direct (CLI) :
#   lumiere-ombre.sh run <action> <cmd...>     # exécute une Lumière
#   lumiere-ombre.sh score [action]            # scoring (Ombre)
#   lumiere-ombre.sh feedback <action>         # feedback lisible
set -uo pipefail

LO_DB="${LO_DB:-$HOME/.jarvis/lumiere-ombre.db}"

_lo_init() {
  mkdir -p "$(dirname "$LO_DB")"
  sqlite3 "$LO_DB" "CREATE TABLE IF NOT EXISTS actions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER, action TEXT, status TEXT, dur_ms INTEGER, out_len INTEGER, note TEXT);
    CREATE INDEX IF NOT EXISTS idx_act ON actions(action,ts);" 2>/dev/null
}

# LUMIÈRE + OMBRE : exécute la commande, journalise (statut = ok si code 0 & sortie non vide)
lo_run() {
  _lo_init
  local action="$1"; shift
  local t0 out rc dur status
  t0=$(date +%s%3N)
  out="$("$@" 2>/dev/null)"; rc=$?
  dur=$(( $(date +%s%3N) - t0 ))
  if [ $rc -eq 0 ] && [ -n "$out" ]; then status=ok; else status=fail; fi
  sqlite3 "$LO_DB" "INSERT INTO actions(ts,action,status,dur_ms,out_len,note)
    VALUES($(date +%s),'${action//\'/}','$status',$dur,${#out},'rc=$rc');" 2>/dev/null
  printf '%s\n' "$out"
  return $rc
}

# Log manuel (pour actions dont tu gères l'exécution toi-même)
lo_log() {  # $1=action $2=status $3=dur_ms $4=out_len $5=note
  _lo_init
  sqlite3 "$LO_DB" "INSERT INTO actions(ts,action,status,dur_ms,out_len,note)
    VALUES($(date +%s),'${1//\'/}','${2:-ok}',${3:-0},${4:-0},'${5:-}');" 2>/dev/null
}

# FEEDBACK : renvoie 0 (=vrai/sauter) si l'action a échoué récemment
lo_should_skip() {  # $1=action $2=fenêtre_min(defaut 30) [$3=statut ciblé, defaut fail]
  _lo_init
  local n
  n=$(sqlite3 "$LO_DB" "SELECT COUNT(*) FROM actions
    WHERE action='${1//\'/}' AND status='${3:-fail}'
    AND ts > $(date +%s) - ${2:-30}*60;" 2>/dev/null)
  [ "${n:-0}" -gt 0 ]
}

# FEEDBACK lisible
lo_feedback() {
  _lo_init
  local a="${1:-}" where=""
  [ -n "$a" ] && where="WHERE action='${a//\'/}'"
  sqlite3 -column -header "$LO_DB" "SELECT action, status, COUNT(*) n,
    ROUND(AVG(dur_ms)) dur_moy_ms, ROUND(AVG(out_len)) out_moy
    FROM actions $where GROUP BY action,status ORDER BY action,n DESC;" 2>/dev/null
}

# --- CLI ---
case "${1:-}" in
  run)      shift; act="$1"; shift; lo_run "$act" "$@" ;;
  score|feedback|--analyze) lo_feedback "${2:-}" ;;
  skip)     lo_should_skip "${2:?action}" "${3:-30}" && echo "SKIP (KO récent)" || echo "GO" ;;
  "") : ;;  # sourcé → ne rien exécuter
  *) echo "usage: lumiere-ombre.sh {run <action> <cmd...>|score [action]|skip <action> [min]}" >&2 ;;
esac
