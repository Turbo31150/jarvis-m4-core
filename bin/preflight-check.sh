#!/usr/bin/env bash
# =============================================================================
# preflight-check.sh  (BL1-052)
# Pre-flight check AVANT démarrage du système JARVIS.
# 100% READ-ONLY : aucune écriture système, aucun restart, aucun effet de bord.
# Seule écriture possible : le log applicatif ~/.local/share/preflight-check.log
# (désactivable via --no-log), qui n'affecte pas l'état de JARVIS.
#
# Exit code = nombre de FAIL (0 = tout bon). Les WARN n'échouent pas.
#
# Usage:
#   preflight-check.sh [--json] [--no-log] [--services "a b c"] [--self-test]
# =============================================================================
set -uo pipefail

# --------------------------------------------------------------------------- #
# Constantes / seuils
# --------------------------------------------------------------------------- #
DISK_MIN_FREE_PCT=5          # < 5% libre => FAIL
RAM_MIN_FREE_MB=500          # < 500 Mo dispo => WARN
GPU_MAX_TEMP_C=88            # >= 88°C => WARN
# 2026-08-18 : LM Studio ne tourne PAS sur M4. Il est sur M6, joignable par le
# cable direct ASIX (RTT 1,4 ms). Sonder 127.0.0.1:1234 rendait un FAIL
# permanent sur un noeud parfaitement sain.
LMS_URL="${LMS_URL:-http://10.42.0.230:1234/v1/models}"
LMS_TIMEOUT=3
HOME_DIR="${HOME}"
LOG_FILE="${HOME_DIR}/.local/share/preflight-check.log"

# Services user critiques (surchargeables via --services)
DEFAULT_SERVICES=(lms-runaway-guard jarvis-planning-widget)

# Bases SQLite clés (label:chemin)
# Au-dela de ce seuil, PRAGMA quick_check/integrity_check ne tient pas dans un
# pre-vol : mesure du 18/08 sur jarvis_master.db (6,5 Go) -> >90 s pour les
# deux, contre 3 ms pour la sonde de schema. On sonde, et on DIT qu on n a
# pas fait le controle profond plutot que d annoncer un "ok" non verifie.
DB_DEEP_MAX_MO="${DB_DEEP_MAX_MO:-512}"

DB_LIST=(
  "jarvis_master:${HOME_DIR}/jarvis/jarvis_master.db"
  "unified_plan:${HOME_DIR}/jarvis/data/unified_plan.db"
)

# --------------------------------------------------------------------------- #
# Options
# --------------------------------------------------------------------------- #
OUT_JSON=0
DO_LOG=1
SELF_TEST=0
SERVICES=("${DEFAULT_SERVICES[@]}")

while [ $# -gt 0 ]; do
  case "$1" in
    --json)      OUT_JSON=1 ;;
    --no-log)    DO_LOG=0 ;;
    --self-test) SELF_TEST=1 ;;
    --services)  shift; [ $# -gt 0 ] && read -r -a SERVICES <<< "$1" ;;
    -h|--help)
      grep -E '^#( |=)' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "Option inconnue: $1" >&2; exit 2 ;;
  esac
  shift
done

# --------------------------------------------------------------------------- #
# Collecte des résultats (parallel arrays pour compat bash 4)
# --------------------------------------------------------------------------- #
declare -a R_NAME R_STATUS R_DETAIL
FAIL_COUNT=0
WARN_COUNT=0
OK_COUNT=0

# add_result <name> <status OK|WARN|FAIL> <detail>
add_result() {
  R_NAME+=("$1"); R_STATUS+=("$2"); R_DETAIL+=("$3")
  case "$2" in
    OK)   OK_COUNT=$((OK_COUNT+1)) ;;
    WARN) WARN_COUNT=$((WARN_COUNT+1)) ;;
    FAIL) FAIL_COUNT=$((FAIL_COUNT+1)) ;;
  esac
}

icon() {
  case "$1" in
    OK)   printf '✅' ;;
    WARN) printf '⚠️' ;;
    FAIL) printf '❌' ;;
    *)    printf '  ' ;;
  esac
}

# JSON string escaper
json_esc() {
  local s=$1
  s=${s//\\/\\\\}
  s=${s//\"/\\\"}
  s=${s//$'\t'/ }
  s=${s//$'\n'/ }
  printf '%s' "$s"
}

# --------------------------------------------------------------------------- #
# CHECKS (tous en lecture seule)
# --------------------------------------------------------------------------- #

check_disk() {
  local mnt="$1" label="$2" pct free_pct used
  if ! df -P "$mnt" >/dev/null 2>&1; then
    add_result "disk:${label}" "WARN" "point de montage introuvable"
    return
  fi
  # Use% column -> capacité utilisée
  used=$(df -P "$mnt" 2>/dev/null | awk 'NR==2{gsub("%","",$5); print $5}')
  [ -z "${used:-}" ] && { add_result "disk:${label}" "WARN" "lecture df impossible"; return; }
  free_pct=$((100 - used))
  local avail_h
  avail_h=$(df -Ph "$mnt" 2>/dev/null | awk 'NR==2{print $4}')
  if [ "$free_pct" -lt "$DISK_MIN_FREE_PCT" ]; then
    add_result "disk:${label}" "FAIL" "libre ${free_pct}% (<${DISK_MIN_FREE_PCT}%) dispo=${avail_h}"
  else
    add_result "disk:${label}" "OK" "libre ${free_pct}% dispo=${avail_h}"
  fi
}

check_ram() {
  local avail_mb
  avail_mb=$(free -m 2>/dev/null | awk '/^Mem:/{print $7}')
  if [ -z "${avail_mb:-}" ]; then
    add_result "ram" "WARN" "lecture free impossible"
    return
  fi
  if [ "$avail_mb" -lt "$RAM_MIN_FREE_MB" ]; then
    add_result "ram" "WARN" "dispo ${avail_mb}Mo (<${RAM_MIN_FREE_MB}Mo)"
  else
    add_result "ram" "OK" "dispo ${avail_mb}Mo"
  fi
}

check_load() {
  local cores load1 limit
  cores=$(nproc 2>/dev/null || echo 1)
  load1=$(awk '{print $1}' /proc/loadavg 2>/dev/null)
  [ -z "${load1:-}" ] && { add_result "loadavg" "WARN" "lecture loadavg impossible"; return; }
  limit=$((cores * 2))
  # comparaison flottante via awk
  if awk -v l="$load1" -v m="$limit" 'BEGIN{exit !(l>=m)}'; then
    add_result "loadavg" "WARN" "load1=${load1} (>= ${limit} = nproc*2)"
  else
    add_result "loadavg" "OK" "load1=${load1} (limite ${limit})"
  fi
}

check_gpu() {
  if ! command -v nvidia-smi >/dev/null 2>&1; then
    add_result "gpu" "OK" "nvidia-smi absent (pas de GPU à vérifier)"
    return
  fi
  local ngpu
  ngpu=$(nvidia-smi -L 2>/dev/null | grep -c '^GPU ' || echo 0)
  if [ "$ngpu" -eq 0 ]; then
    add_result "gpu" "WARN" "nvidia-smi présent mais aucun GPU listé"
    return
  fi
  local maxt
  maxt=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits 2>/dev/null \
          | awk 'BEGIN{m=-1}{if($1+0>m)m=$1+0}END{print m}')
  if [ -z "${maxt:-}" ] || [ "$maxt" = "-1" ]; then
    add_result "gpu" "OK" "${ngpu} GPU présents (température illisible)"
    return
  fi
  if [ "$maxt" -ge "$GPU_MAX_TEMP_C" ]; then
    add_result "gpu" "WARN" "${ngpu} GPU, tmax=${maxt}°C (>=${GPU_MAX_TEMP_C}°C)"
  else
    add_result "gpu" "OK" "${ngpu} GPU, tmax=${maxt}°C"
  fi
}

check_services() {
  local svc st
  for svc in "${SERVICES[@]}"; do
    [ -z "$svc" ] && continue
    st=$(systemctl --user is-active "$svc" 2>/dev/null || true)
    if [ "$st" = "active" ]; then
      add_result "service:${svc}" "OK" "active"
    else
      add_result "service:${svc}" "WARN" "état=${st:-inconnu}"
    fi
  done
}

check_lms() {
  if ! command -v curl >/dev/null 2>&1; then
    add_result "lmstudio" "WARN" "curl absent"
    return
  fi
  local code
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time "$LMS_TIMEOUT" "$LMS_URL" 2>/dev/null || echo 000)
  if [ "$code" = "200" ]; then
    add_result "lmstudio" "OK" "M1 ${LMS_URL} HTTP ${code}"
  else
    add_result "lmstudio" "WARN" "M1 DOWN (${LMS_URL} HTTP ${code})"
  fi
}

check_sqlite() {
  local entry label path res
  for entry in "${DB_LIST[@]}"; do
    label=${entry%%:*}
    path=${entry#*:}
    if [ ! -f "$path" ]; then
      add_result "db:${label}" "WARN" "fichier absent (${path})"
      continue
    fi
    if ! command -v sqlite3 >/dev/null 2>&1; then
      add_result "db:${label}" "WARN" "sqlite3 absent"
      continue
    fi
    # Ouverture STRICTEMENT read-only + immutable pour ne poser aucun verrou.
    taille_mo=$(( $(stat -Lc%s "$path" 2>/dev/null || echo 0) / 1048576 ))  # -L : les bases sont des liens vers ~/jarvis/databases/
    sonde=$(timeout 10 sqlite3 "file:${path}?mode=ro&immutable=1" \
              'PRAGMA schema_version;' 2>/dev/null | head -n1)
    if [ -z "$sonde" ]; then
      add_result "db:${label}" "FAIL" "base illisible (${taille_mo} Mo)"
      continue
    fi
    if [ "$taille_mo" -le "$DB_DEEP_MAX_MO" ]; then
      res=$(timeout 60 sqlite3 "file:${path}?mode=ro&immutable=1" 'PRAGMA quick_check;' 2>/dev/null | head -n1)
      if [ "$res" = "ok" ]; then
        add_result "db:${label}" "OK" "quick_check ok (${taille_mo} Mo)"
      elif [ -z "$res" ]; then
        add_result "db:${label}" "WARN" "quick_check interrompu au plafond 60 s (${taille_mo} Mo)"
      else
        add_result "db:${label}" "FAIL" "quick_check: ${res}"
      fi
    else
      add_result "db:${label}" "OK" "ouvrable, schema lisible — controle profond NON fait (${taille_mo} Mo > ${DB_DEEP_MAX_MO} Mo)"
    fi
  done
}

run_all_checks() {
  check_disk "/"        "root"
  check_disk "$HOME_DIR" "home"
  check_ram
  check_load
  check_gpu
  check_services
  check_lms
  check_sqlite
}

# --------------------------------------------------------------------------- #
# Rendus
# --------------------------------------------------------------------------- #
render_text() {
  local i verdict
  echo "=== JARVIS PRE-FLIGHT CHECK (BL1-052) ==="
  echo "date=$(date -Is)  host=$(hostname)  read-only"
  echo "-----------------------------------------"
  for i in "${!R_NAME[@]}"; do
    printf '%s  %-22s %s\n' "$(icon "${R_STATUS[$i]}")" "${R_NAME[$i]}" "${R_DETAIL[$i]}"
  done
  echo "-----------------------------------------"
  if [ "$FAIL_COUNT" -eq 0 ]; then verdict="GO"; else verdict="NO-GO"; fi
  echo "RESUME: OK=${OK_COUNT} WARN=${WARN_COUNT} FAIL=${FAIL_COUNT}  =>  VERDICT: ${verdict}"
  echo "exit_code=${FAIL_COUNT}"
}

render_json() {
  local i verdict first=1
  if [ "$FAIL_COUNT" -eq 0 ]; then verdict="GO"; else verdict="NO-GO"; fi
  printf '{'
  printf '"checks":['
  for i in "${!R_NAME[@]}"; do
    [ "$first" -eq 0 ] && printf ','
    first=0
    printf '{"name":"%s","status":"%s","detail":"%s"}' \
      "$(json_esc "${R_NAME[$i]}")" "${R_STATUS[$i]}" "$(json_esc "${R_DETAIL[$i]}")"
  done
  printf '],'
  printf '"summary":{"ok":%d,"warn":%d,"fail":%d},' "$OK_COUNT" "$WARN_COUNT" "$FAIL_COUNT"
  printf '"verdict":"%s","exit_code":%d}\n' "$verdict" "$FAIL_COUNT"
}

write_log() {
  [ "$DO_LOG" -eq 1 ] || return 0
  mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || return 0
  printf '%s verdict=%s ok=%d warn=%d fail=%d\n' \
    "$(date -Is)" \
    "$([ "$FAIL_COUNT" -eq 0 ] && echo GO || echo NO-GO)" \
    "$OK_COUNT" "$WARN_COUNT" "$FAIL_COUNT" >> "$LOG_FILE" 2>/dev/null || true
}

# --------------------------------------------------------------------------- #
# SELF-TEST : exécute sur l'environnement réel, valide la structure de sortie.
# --------------------------------------------------------------------------- #
self_test() {
  local script="$0" out rc jout jrc problems=0
  # --- run texte réel (sans log pour rester non-intrusif) ---
  out=$("$script" --no-log 2>&1); rc=$?

  # sections attendues
  for needle in "PRE-FLIGHT CHECK" "RESUME:" "VERDICT:" "exit_code="; do
    if ! grep -qF "$needle" <<< "$out"; then
      echo "SELFTEST: section manquante -> '$needle'"; problems=$((problems+1))
    fi
  done
  # au moins un check attendu présent
  for needle in "disk:root" "disk:home" "ram" "loadavg" "gpu" "lmstudio" "db:jarvis_master"; do
    if ! grep -qF "$needle" <<< "$out"; then
      echo "SELFTEST: check manquant -> '$needle'"; problems=$((problems+1))
    fi
  done
  # cohérence exit_code texte <-> rc
  local declared
  declared=$(grep -oE 'exit_code=[0-9]+' <<< "$out" | tail -n1 | cut -d= -f2)
  if [ "${declared:-x}" != "$rc" ]; then
    echo "SELFTEST: exit_code affiché(${declared:-?}) != rc réel(${rc})"; problems=$((problems+1))
  fi
  # rc doit être un entier >= 0
  if ! [[ "$rc" =~ ^[0-9]+$ ]]; then
    echo "SELFTEST: rc non entier (${rc})"; problems=$((problems+1))
  fi

  # --- run json réel ---
  jout=$("$script" --json --no-log 2>&1); jrc=$?
  if command -v python3 >/dev/null 2>&1; then
    if ! python3 -c 'import json,sys; d=json.load(sys.stdin); assert "checks" in d and "verdict" in d and "exit_code" in d and "summary" in d' <<< "$jout" 2>/dev/null; then
      echo "SELFTEST: JSON invalide ou clés manquantes"; problems=$((problems+1))
    fi
  else
    grep -qF '"verdict"' <<< "$jout" || { echo "SELFTEST: JSON sans verdict"; problems=$((problems+1)); }
  fi
  if [ "$jrc" != "$rc" ]; then
    echo "SELFTEST: exit code json(${jrc}) != texte(${rc})"; problems=$((problems+1))
  fi

  if [ "$problems" -eq 0 ]; then
    echo "SELFTEST OK (exit_code_reel=${rc}, ok=$(grep -oE 'OK=[0-9]+' <<<"$out"|cut -d= -f2), warn=$(grep -oE 'WARN=[0-9]+' <<<"$out"|cut -d= -f2), fail=$(grep -oE 'FAIL=[0-9]+' <<<"$out"|cut -d= -f2))"
    exit 0
  else
    echo "SELFTEST ECHEC (${problems} problème(s))"
    exit 1
  fi
}

# --------------------------------------------------------------------------- #
# MAIN
# --------------------------------------------------------------------------- #
if [ "$SELF_TEST" -eq 1 ]; then
  self_test
fi

run_all_checks
write_log

if [ "$OUT_JSON" -eq 1 ]; then
  render_json
else
  render_text
fi

exit "$FAIL_COUNT"
