#!/usr/bin/env bash
#
# docker-connrefused-restart.sh  (BL1-003)
# ----------------------------------------
# Surveille la connectivite des ports exposes des containers Docker et
# redemarre ceux en "Connection refused" / timeout, avec garde-fous stricts :
#   - max 2 restarts par container et par run
#   - cooldown 5 min persiste (ne re-restart pas un container restarte < 5 min)
#   - denylist de containers critiques jamais redemarres
#   - --dry-run par defaut (aucun restart tant que --once/--daemon absent)
#
# Modes :
#   --dry-run            detecte les KO et montre ce qui SERAIT restarte (defaut)
#   --once               un cycle reel (restarts autorises)
#   --daemon             boucle infinie, INTERVAL=60s
#   --self-test          teste la logique sans toucher a Docker (SELFTEST=1)
#
# Options :
#   --containers "n1 n2" liste explicite a surveiller (defaut: auto)
#   --protect   "n1 n2"  ajoute des containers a la denylist
#   --interval  N        daemon: secondes entre cycles (defaut 60)
#
# Sorties : log  ~/.local/share/docker-connrefused-restart.log
#           state ~/.local/share/docker-connrefused-restart.state
#
# Robuste : docker absent / daemon down / nc|curl manquant => log clair, exit 0.
#
set -euo pipefail

# ----------------------------------------------------------------------------
# Constantes & chemins
# ----------------------------------------------------------------------------
readonly COOLDOWN_SECONDS=300          # 5 min
readonly MAX_RESTARTS_PER_RUN=2        # par container et par run
readonly CONNECT_TIMEOUT=3             # secondes par test de port
INTERVAL="${INTERVAL:-60}"             # daemon

DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}"
LOG_FILE="${LOG_FILE:-$DATA_DIR/docker-connrefused-restart.log}"
STATE_FILE="${STATE_FILE:-$DATA_DIR/docker-connrefused-restart.state}"

# Denylist par defaut : services critiques + bases de donnees courantes.
DEFAULT_DENYLIST=(
  aria-sentinel orion
  postgres postgresql mysql mariadb mongo mongodb redis
  clickhouse cassandra elasticsearch influxdb timescaledb
)

# Etat runtime
declare -A RESTARTS_THIS_RUN=()        # container -> nb restarts effectues ce run
MODE="dry-run"                          # dry-run | once | daemon | self-test
WATCH_CONTAINERS=""                     # liste explicite (sinon auto)
EXTRA_PROTECT=""                        # containers ajoutes a la denylist
MISSING_TOOLS=""                        # outils manquants documentes
HAVE_NC=0
HAVE_CURL=0

# ----------------------------------------------------------------------------
# Log
# ----------------------------------------------------------------------------
log() {
  local level="$1"; shift
  local ts; ts="$(date '+%Y-%m-%d %H:%M:%S')"
  local line="[$ts] [$level] $*"
  if mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null; then
    printf '%s\n' "$line" >>"$LOG_FILE" 2>/dev/null || true
  fi
  printf '%s\n' "$line"
}

# ----------------------------------------------------------------------------
# State : container<TAB>last_restart_epoch
# ----------------------------------------------------------------------------
state_last_restart() {  # $1=container -> echo epoch (0 si inconnu)
  local c="$1"
  [[ -f "$STATE_FILE" ]] || { echo 0; return; }
  local epoch
  epoch="$(awk -F'\t' -v c="$c" '$1==c{v=$2} END{print v+0}' "$STATE_FILE" 2>/dev/null || echo 0)"
  echo "${epoch:-0}"
}

state_record_restart() {  # $1=container  (met a jour l'epoch a maintenant)
  local c="$1" now; now="$(date +%s)"
  mkdir -p "$(dirname "$STATE_FILE")" 2>/dev/null || true
  local tmp; tmp="$(mktemp "${STATE_FILE}.XXXXXX")"
  if [[ -f "$STATE_FILE" ]]; then
    awk -F'\t' -v c="$c" '$1!=c{print}' "$STATE_FILE" >"$tmp" 2>/dev/null || true
  fi
  printf '%s\t%s\n' "$c" "$now" >>"$tmp"
  mv -f "$tmp" "$STATE_FILE"
}

# ----------------------------------------------------------------------------
# Denylist
# ----------------------------------------------------------------------------
is_protected() {  # $1=container
  local c="$1" p
  for p in "${DEFAULT_DENYLIST[@]}"; do
    [[ "$c" == "$p" ]] && return 0
    # match large : nom contenant un motif base de donnees / service critique
    case "$c" in *"$p"*) return 0;; esac
  done
  for p in $EXTRA_PROTECT; do
    [[ "$c" == "$p" ]] && return 0
  done
  return 1
}

# ----------------------------------------------------------------------------
# Outils de connectivite
# ----------------------------------------------------------------------------
detect_tools() {
  HAVE_NC=0; HAVE_CURL=0
  if command -v nc >/dev/null 2>&1; then HAVE_NC=1; else MISSING_TOOLS="$MISSING_TOOLS nc"; fi
  if command -v curl >/dev/null 2>&1; then HAVE_CURL=1; else MISSING_TOOLS="$MISSING_TOOLS curl"; fi
  if [[ $HAVE_NC -eq 0 && $HAVE_CURL -eq 0 ]]; then
    log WARN "Ni 'nc' ni 'curl' disponibles -> impossible de tester les ports. Manquants:${MISSING_TOOLS}. Installez netcat-openbsd ou curl."
    return 1
  fi
  [[ -n "$MISSING_TOOLS" ]] && log INFO "Outils manquants (non bloquant):${MISSING_TOOLS}"
  return 0
}

# Normalise un host issu de 'docker port' : retire les crochets IPv6 et
# mappe les adresses "wildcard" (0.0.0.0, ::) et vide sur la loopback.
normalize_host() {  # $1=host -> echo host testable
  local host="$1"
  host="${host#[}"; host="${host%]}"           # [::] -> ::
  case "$host" in
    0.0.0.0|::|"") echo "127.0.0.1" ;;
    *)             echo "$host" ;;
  esac
}

# Teste host:port. Retourne 0 si OK (ouvert), 1 si KO (refused/timeout).
probe_hostport() {  # $1=host $2=port
  local host port
  host="$(normalize_host "$1")"; port="$2"
  if [[ ${HAVE_NC:-0} -eq 1 ]]; then
    nc -z -w "$CONNECT_TIMEOUT" "$host" "$port" >/dev/null 2>&1 && return 0
    return 1
  fi
  if [[ ${HAVE_CURL:-0} -eq 1 ]]; then
    # On ne juge QUE la connexion TCP : 7=refused, 28=timeout => KO.
    local rc=0
    curl -s -o /dev/null --connect-timeout "$CONNECT_TIMEOUT" \
         "http://${host}:${port}/" >/dev/null 2>&1 || rc=$?
    [[ $rc -eq 7 || $rc -eq 28 ]] && return 1
    return 0
  fi
  return 1
}

# Renvoie les host:port exposes d'un container (un par ligne), ou rien.
container_hostports() {  # $1=container
  local c="$1"
  docker port "$c" 2>/dev/null | sed -n 's/.*-> \(.*\)/\1/p'
}

# Teste un container : 0 = OK, 1 = KO.
# Agrege par PORT : un port ecoute a la fois en IPv4 (0.0.0.0) et IPv6 ([::])
# n'est KO que si AUCUNE de ses adresses ne repond (evite les faux positifs).
# Un container sans port expose est considere OK (rien a tester).
check_container() {  # $1=container
  local c="$1" hp host port any=0 ko=0 p
  local -A port_ok=()
  local -A port_seen=()
  while IFS= read -r hp; do
    [[ -z "$hp" ]] && continue
    any=1
    host="${hp%:*}"; port="${hp##*:}"
    port_seen[$port]=1
    if probe_hostport "$host" "$port"; then
      port_ok[$port]=1
      log INFO "OK   $c -> $host:$port"
    fi
  done < <(container_hostports "$c")
  [[ $any -eq 0 ]] && { log INFO "SKIP $c (aucun port expose)"; return 0; }
  for p in "${!port_seen[@]}"; do
    if [[ "${port_ok[$p]:-0}" != "1" ]]; then
      log WARN "KO   $c -> port $p injoignable sur toutes ses adresses (connection refused/timeout)"
      ko=1
    fi
  done
  return $ko
}

# ----------------------------------------------------------------------------
# Selection des containers a surveiller
# ----------------------------------------------------------------------------
auto_containers() {
  # Tous les containers Up ayant au moins un port publie.
  local c
  docker ps --filter status=running --format '{{.Names}}' 2>/dev/null | while IFS= read -r c; do
    [[ -z "$c" ]] && continue
    [[ -n "$(container_hostports "$c")" ]] && echo "$c"
  done
}

list_watch() {
  if [[ -n "$WATCH_CONTAINERS" ]]; then
    printf '%s\n' $WATCH_CONTAINERS
  else
    auto_containers
  fi
}

# ----------------------------------------------------------------------------
# Decision de restart (coeur de la logique, testable)
#   Retourne :
#     0 = restart decide (dry) / effectue (reel)
#     2 = bloque (protege / max / cooldown)  -> raison via $DECISION_REASON
#   Ordre des garde-fous : denylist > max/run > cooldown.
# ----------------------------------------------------------------------------
DECISION_REASON=""
decide_and_restart() {  # $1=container  $2=do_real (0/1)
  local c="$1" do_real="$2" now last delta count
  DECISION_REASON=""

  if is_protected "$c"; then
    DECISION_REASON="protege (denylist)"; return 2
  fi

  count="${RESTARTS_THIS_RUN[$c]:-0}"
  if (( count >= MAX_RESTARTS_PER_RUN )); then
    DECISION_REASON="max ${MAX_RESTARTS_PER_RUN} restarts atteint ce run"; return 2
  fi

  now="$(date +%s)"
  last="$(state_last_restart "$c")"
  delta=$(( now - last ))
  if (( last > 0 && delta < COOLDOWN_SECONDS )); then
    DECISION_REASON="cooldown ($((COOLDOWN_SECONDS - delta))s restants)"; return 2
  fi

  # A ce stade, un restart est LEGITIME.
  if [[ "$do_real" -eq 1 ]]; then
    log ACTION "RESTART $c"
    if [[ "${SELFTEST:-0}" == "1" ]]; then
      : # self-test : ne touche jamais a Docker
    else
      docker restart "$c" >/dev/null 2>&1 || { log ERROR "echec docker restart $c"; return 2; }
    fi
    state_record_restart "$c"
    RESTARTS_THIS_RUN[$c]=$(( count + 1 ))
  else
    log DRYRUN "SERAIT restarte: $c"
  fi
  return 0
}

# ----------------------------------------------------------------------------
# Verif Docker
# ----------------------------------------------------------------------------
docker_ready() {
  if ! command -v docker >/dev/null 2>&1; then
    log WARN "binaire 'docker' introuvable -> rien a faire."
    return 1
  fi
  if ! docker info >/dev/null 2>&1; then
    log WARN "daemon Docker injoignable (info KO) -> rien a faire."
    return 1
  fi
  return 0
}

# ----------------------------------------------------------------------------
# Cycle
# ----------------------------------------------------------------------------
run_cycle() {  # $1=do_real (0/1)
  local do_real="$1" c
  local -a watch=()
  mapfile -t watch < <(list_watch)

  if [[ ${#watch[@]} -eq 0 ]]; then
    log INFO "Aucun container a surveiller."
    return 0
  fi

  log INFO "Surveillance de ${#watch[@]} container(s): ${watch[*]}"
  for c in "${watch[@]}"; do
    [[ -z "$c" ]] && continue
    if check_container "$c"; then
      continue   # OK
    fi
    # KO detecte
    if decide_and_restart "$c" "$do_real"; then
      :
    else
      log SKIP "restart bloque pour $c : $DECISION_REASON"
    fi
  done
  return 0
}

# ----------------------------------------------------------------------------
# SELF-TEST : valide la logique sans Docker reel (SELFTEST=1)
#   Chaque garde-fou est teste ISOLEMENT (etat & compteur reinitialises).
# ----------------------------------------------------------------------------
self_test() {
  export SELFTEST=1
  local fails=0
  local tdir; tdir="$(mktemp -d)"
  STATE_FILE="$tdir/state"
  LOG_FILE="$tdir/log"
  local fake="selftest-fake-ko"

  log INFO "SELFTEST: demarrage (aucun vrai container touche)"

  # 1) KO en dry-run => restart DECIDE, mais AUCUN etat ecrit (rien restarte).
  RESTARTS_THIS_RUN=(); : >"$STATE_FILE"
  if decide_and_restart "$fake" 0; then
    log INFO "SELFTEST 1 OK: dry-run decide un restart (sans agir)"
  else
    log ERROR "SELFTEST 1 FAIL: dry-run n'a pas decide de restart ($DECISION_REASON)"; fails=1
  fi
  if [[ -s "$STATE_FILE" ]]; then
    log ERROR "SELFTEST 1 FAIL: dry-run a ecrit dans le state"; fails=1
  fi

  # 2) restart reel (simule) accepte 1x, compteur incremente, state enregistre.
  RESTARTS_THIS_RUN=(); : >"$STATE_FILE"
  if decide_and_restart "$fake" 1 && [[ "${RESTARTS_THIS_RUN[$fake]:-0}" -eq 1 ]]; then
    log INFO "SELFTEST 2 OK: restart reel (simule) accepte et compte=1"
  else
    log ERROR "SELFTEST 2 FAIL: restart reel non applique (compte=${RESTARTS_THIS_RUN[$fake]:-0})"; fails=1
  fi

  # 3) cooldown : juste apres le restart du test 2 => refuse (< 5 min).
  if decide_and_restart "$fake" 1; then
    log ERROR "SELFTEST 3 FAIL: cooldown non respecte"; fails=1
  elif [[ "$DECISION_REASON" == cooldown* ]]; then
    log INFO "SELFTEST 3 OK: cooldown 5 min respecte ($DECISION_REASON)"
  else
    log ERROR "SELFTEST 3 FAIL: refus mais mauvaise raison ($DECISION_REASON)"; fails=1
  fi

  # 4) max restarts/run (isole du cooldown : state vierge, compteur deja a 2).
  RESTARTS_THIS_RUN=(); : >"$STATE_FILE"
  RESTARTS_THIS_RUN[$fake]=$MAX_RESTARTS_PER_RUN
  if decide_and_restart "$fake" 1; then
    log ERROR "SELFTEST 4 FAIL: max ${MAX_RESTARTS_PER_RUN}/run non respecte"; fails=1
  elif [[ "$DECISION_REASON" == max* ]]; then
    log INFO "SELFTEST 4 OK: max ${MAX_RESTARTS_PER_RUN} restarts/run respecte ($DECISION_REASON)"
  else
    log ERROR "SELFTEST 4 FAIL: refus mais mauvaise raison ($DECISION_REASON)"; fails=1
  fi

  # 5) denylist critique : aria-sentinel jamais restarte.
  RESTARTS_THIS_RUN=(); : >"$STATE_FILE"
  if decide_and_restart "aria-sentinel" 1; then
    log ERROR "SELFTEST 5 FAIL: container protege restarte !"; fails=1
  elif [[ "$DECISION_REASON" == protege* ]]; then
    log INFO "SELFTEST 5 OK: denylist respectee ($DECISION_REASON)"
  else
    log ERROR "SELFTEST 5 FAIL: refus mais mauvaise raison ($DECISION_REASON)"; fails=1
  fi

  # 6) base de donnees via match large (prod-postgres-1).
  RESTARTS_THIS_RUN=(); : >"$STATE_FILE"
  if decide_and_restart "prod-postgres-1" 1; then
    log ERROR "SELFTEST 6 FAIL: base de donnees restartee !"; fails=1
  else
    log INFO "SELFTEST 6 OK: base de donnees protegee ($DECISION_REASON)"
  fi

  # 7) --protect surchargeable.
  RESTARTS_THIS_RUN=(); : >"$STATE_FILE"; EXTRA_PROTECT="mon-service"
  if decide_and_restart "mon-service" 1; then
    log ERROR "SELFTEST 7 FAIL: --protect ignore !"; fails=1
  else
    log INFO "SELFTEST 7 OK: --protect respecte ($DECISION_REASON)"
  fi
  EXTRA_PROTECT=""

  # 8) normalisation IPv6 : [::] -> loopback (pas de faux KO).
  if [[ "$(normalize_host '[::]')" == "127.0.0.1" && "$(normalize_host '0.0.0.0')" == "127.0.0.1" ]]; then
    log INFO "SELFTEST 8 OK: normalisation host wildcard/IPv6 -> loopback"
  else
    log ERROR "SELFTEST 8 FAIL: normalisation host incorrecte"; fails=1
  fi

  rm -rf "$tdir" 2>/dev/null || true
  if [[ $fails -eq 0 ]]; then
    echo "SELFTEST OK"
    return 0
  fi
  echo "SELFTEST FAIL"
  return 1
}

# ----------------------------------------------------------------------------
# Args
# ----------------------------------------------------------------------------
usage() {
  cat <<'EOF'
Usage: docker-connrefused-restart.sh [MODE] [OPTIONS]
Modes  : --dry-run (defaut) | --once | --daemon | --self-test
Options: --containers "n1 n2"  liste a surveiller (defaut: auto)
         --protect    "n1 n2"  containers a proteger en plus de la denylist
         --interval N          daemon: secondes entre cycles (defaut 60)
         -h|--help
EOF
}

parse_args() {
  local got_mode=0
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --dry-run)    MODE="dry-run";   got_mode=1;;
      --once)       MODE="once";      got_mode=1;;
      --daemon)     MODE="daemon";    got_mode=1;;
      --self-test)  MODE="self-test"; got_mode=1;;
      --containers) WATCH_CONTAINERS="${2:-}"; shift;;
      --protect)    EXTRA_PROTECT="${2:-}"; shift;;
      --interval)   INTERVAL="${2:-60}"; shift;;
      -h|--help)    usage; exit 0;;
      *) log ERROR "argument inconnu: $1"; usage; exit 2;;
    esac
    shift
  done
  if [[ $got_mode -eq 0 ]]; then
    MODE="dry-run"   # defaut si aucun arg de mode
  fi
}

# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
main() {
  parse_args "$@"
  mkdir -p "$DATA_DIR" 2>/dev/null || true

  if [[ "$MODE" == "self-test" ]]; then
    self_test
    exit $?
  fi

  log INFO "=== demarrage mode=$MODE (protect suppl.: '${EXTRA_PROTECT:-}') ==="

  if ! docker_ready; then
    log INFO "Docker indisponible: sortie propre (exit 0)."
    exit 0
  fi
  if ! detect_tools; then
    log INFO "Aucun outil de sonde: sortie propre (exit 0)."
    exit 0
  fi

  case "$MODE" in
    dry-run) run_cycle 0 ;;
    once)    run_cycle 1 ;;
    daemon)
      log INFO "daemon: cycle toutes les ${INTERVAL}s"
      while true; do
        RESTARTS_THIS_RUN=()      # compteur max reset a chaque cycle
        run_cycle 1
        sleep "$INTERVAL"
      done
      ;;
  esac
  log INFO "=== fin mode=$MODE ==="
}

main "$@"
