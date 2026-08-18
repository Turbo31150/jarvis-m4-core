#!/usr/bin/env bash
# cli-skills-run-all.sh — lance TOUS les skills cli_skill_* d'un coup et rend un tableau d'etat.
#
# Cree le 2026-08-18. Chaque skill est lance en isolation, avec un delai maximum,
# et son resultat classe : OK (sortie utile), VIDE (rc=0 mais rien), ECHEC (rc!=0),
# TIMEOUT. Aucune action sortante n'est declenchee : les skills de publication sont
# invoques sans argument, donc en mode diagnostic.
#
# Usage :
#   cli-skills-run-all.sh                 # tous les skills, 60 s chacun
#   cli-skills-run-all.sh --timeout 120   # delai par skill
#   cli-skills-run-all.sh --only search,gpu,health
#   cli-skills-run-all.sh --verbose       # affiche la sortie complete de chaque skill
set -uo pipefail

SKILLS_DIR="${HOME}/.claude/skills"
OUT_DIR="${HOME}/jarvis/logs/cli-skills"
DB="${HOME}/jarvis/db/cli_history.db"
TIMEOUT=60
ONLY=""
VERBOSE=0

while [ $# -gt 0 ]; do
  case "$1" in
    --timeout) TIMEOUT="${2:-60}"; shift 2 ;;
    --only)    ONLY="${2:-}"; shift 2 ;;
    --verbose|-v) VERBOSE=1; shift ;;
    --help|-h) sed -n '2,16p' "$0"; exit 0 ;;
    *) echo "argument inconnu : $1" >&2; exit 2 ;;
  esac
done

mkdir -p "$OUT_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
RAPPORT="$OUT_DIR/run-all-$STAMP.md"

liste_skills() {
  local d n
  for d in "$SKILLS_DIR"/cli_skill_*/; do
    [ -d "$d" ] || continue
    n="$(basename "$d")"
    if [ -n "$ONLY" ]; then
      case ",$ONLY," in
        *",${n#cli_skill_},"*) ;;
        *",$n,"*) ;;
        *) continue ;;
      esac
    fi
    printf '%s\n' "$n"
  done
}

entrypoint() {  # $1 = nom du skill -> chemin du point d'entree, vide si aucun
  local d="$SKILLS_DIR/$1"
  if   [ -f "$d/run.sh" ];    then printf '%s\n' "$d/run.sh"
  elif [ -f "$d/driver.sh" ]; then printf '%s\n' "$d/driver.sh"
  fi
}

printf '# Lancement groupe des skills CLI — %s\n\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')" > "$RAPPORT"
printf '| Skill | Etat | rc | Lignes | Extrait |\n|---|---|---|---|---|\n' >> "$RAPPORT"

n_ok=0; n_vide=0; n_echec=0; n_timeout=0; n_absent=0
printf '%-22s %-9s %4s  %s\n' "SKILL" "ETAT" "RC" "PREMIERE LIGNE UTILE"
printf '%.0s─' {1..96}; printf '\n'

while read -r skill; do
  ep="$(entrypoint "$skill")"
  if [ -z "$ep" ]; then
    printf '%-22s %-9s %4s  %s\n' "$skill" "ABSENT" "-" "aucun run.sh ni driver.sh"
    printf '| %s | ABSENT | - | 0 | aucun point d entree |\n' "$skill" >> "$RAPPORT"
    n_absent=$((n_absent+1)); continue
  fi

  log="$OUT_DIR/$skill-$STAMP.log"
  timeout "$TIMEOUT" bash "$ep" > "$log" 2>&1
  rc=$?

  lignes=$(grep -cvE '^\s*$' "$log" 2>/dev/null || echo 0)
  premiere=$(grep -vE '^\s*$' "$log" 2>/dev/null | head -1 | cut -c1-58)

  if   [ "$rc" -eq 124 ]; then etat="TIMEOUT"; n_timeout=$((n_timeout+1))
  elif [ "$rc" -ne 0 ];   then etat="ECHEC";   n_echec=$((n_echec+1))
  elif [ "$lignes" -eq 0 ]; then etat="VIDE";  n_vide=$((n_vide+1))
  else etat="OK"; n_ok=$((n_ok+1))
  fi

  printf '%-22s %-9s %4s  %s\n' "$skill" "$etat" "$rc" "${premiere:-(aucune sortie)}"
  printf '| %s | %s | %s | %s | %s |\n' "$skill" "$etat" "$rc" "$lignes" \
    "$(printf '%s' "${premiere:-—}" | sed 's/|/\\|/g')" >> "$RAPPORT"

  [ "$VERBOSE" -eq 1 ] && { echo "   ┌─ sortie ─"; sed 's/^/   │ /' "$log" | head -25; echo "   └─"; }
done < <(liste_skills)

total=$((n_ok+n_vide+n_echec+n_timeout+n_absent))
printf '%.0s─' {1..96}; printf '\n'
printf 'TOTAL %s  ·  OK %s  ·  VIDE %s  ·  ECHEC %s  ·  TIMEOUT %s  ·  ABSENT %s\n' \
  "$total" "$n_ok" "$n_vide" "$n_echec" "$n_timeout" "$n_absent"
printf '\nrapport : %s\njournaux : %s/*-%s.log\n' "$RAPPORT" "$OUT_DIR" "$STAMP"

{
  printf '\n**Total %s** — OK %s · VIDE %s · ECHEC %s · TIMEOUT %s · ABSENT %s\n' \
    "$total" "$n_ok" "$n_vide" "$n_echec" "$n_timeout" "$n_absent"
} >> "$RAPPORT"

# journalisation du lancement groupe
if command -v sqlite3 >/dev/null 2>&1; then
  mkdir -p "$(dirname "$DB")"
  sqlite3 "$DB" <<SQL 2>/dev/null || true
CREATE TABLE IF NOT EXISTS skill_invocations (
  id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER, skill_name TEXT NOT NULL,
  invoked_at DATETIME DEFAULT CURRENT_TIMESTAMP, trigger_phrase TEXT,
  outcome TEXT, feedback_score INTEGER);
INSERT INTO skill_invocations (skill_name, invoked_at, outcome, trigger_phrase)
VALUES ('cli-skills-run-all', '$(date '+%Y-%m-%d %H:%M:%S %Z')',
        '$([ "$n_echec" -eq 0 ] && [ "$n_timeout" -eq 0 ] && echo success || echo partial)',
        'total=$total ok=$n_ok vide=$n_vide echec=$n_echec timeout=$n_timeout absent=$n_absent');
SQL
fi

[ "$n_echec" -gt 0 ] || [ "$n_timeout" -gt 0 ] && exit 1
exit 0
