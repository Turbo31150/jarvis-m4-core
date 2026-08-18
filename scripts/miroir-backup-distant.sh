#!/usr/bin/env bash
# Miroir hors machine des sauvegardes horaires JARVIS (M1 -> remjarvis-server).
#
# Envoie les N lots les plus recents vers ~/backups-m1/ sur la cible, applique
# une rotation distante, verifie l'integrite sha256 cote distant, puis execute
# un test de restauration REEL sur M1 a partir d'un fichier rapatrie.
#
# La cible est saturee en permanence (load ~4 sur 4 coeurs) : tout transfert est
# bride (rsync --bwlimit) et toute commande distante passe par nice/ionice.
# sqlite3 n'existe PAS sur la cible : le test de restauration se fait sur M1.
#
# Sortie non nulle des qu'une etape echoue.
set -uo pipefail

SRC_DIR="/home/pamerys/jarvis/backups/hourly"
LOG_FILE="/home/pamerys/jarvis/logs/miroir-backup.log"
STATE_FILE="/home/pamerys/jarvis/backups/.miroir-verified"
REMOTE="remjarvis-server"
REMOTE_DIR="backups-m1"          # relatif au HOME distant, jamais absolu
KEEP=12
BWLIMIT=3000                      # Ko/s
SSH_OPTS=(-o BatchMode=yes -o ConnectTimeout=20 -o ServerAliveInterval=30)

VERIFY_ALL=0
SKIP_RESTORE_TEST=0
for arg in "$@"; do
  case "$arg" in
    --verify-all)        VERIFY_ALL=1 ;;
    --no-restore-test)   SKIP_RESTORE_TEST=1 ;;
    -h|--help)
      echo "usage: $0 [--verify-all] [--no-restore-test]"; exit 0 ;;
    *) echo "option inconnue: $arg" >&2; exit 2 ;;
  esac
done

mkdir -p "$(dirname "$LOG_FILE")"
RUN_ID="$(date +%Y%m%d_%H%M%S)"
log() { printf '%s [%s] %s\n' "$(date '+%F %T')" "$RUN_ID" "$*" | tee -a "$LOG_FILE"; }
fail() { log "ECHEC: $*"; exit 1; }

# Verrou anti-concurrence. Le timer porte Persistent=true : tout redemarrage du
# timer (reboot, reconciliation systemd) provoque un rattrapage immediat, qui
# peut croiser un run deja en cours. Constate le 2026-08-01 : deux rsync ont
# ecrit simultanement dans le meme repertoire distant.
LOCK_FILE="/home/pamerys/jarvis/logs/.miroir-backup.lock"
exec 9>"$LOCK_FILE" || { echo "verrou inaccessible: $LOCK_FILE" >&2; exit 1; }
if ! flock -n 9; then
  log "run ignore : une autre instance detient deja le verrou"
  exit 0
fi

TMP_DIR="$(mktemp -d /tmp/miroir-backup.XXXXXX)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

log "=== debut miroir (garde $KEEP lots, bwlimit ${BWLIMIT}ko/s) ==="

# --- 1. selection des lots -----------------------------------------------
[[ -d "$SRC_DIR" ]] || fail "source introuvable: $SRC_DIR"

# Seuls les lots horaires (MANIFEST_AAAAMMJJ_HHMMSS.sha256) sont candidats :
# le repertoire contient aussi des lots d'un autre type (MANIFEST_session_*).
mapfile -t CANDIDATES < <(
  find "$SRC_DIR" -maxdepth 1 -type f -name 'MANIFEST_*.sha256' -printf '%f\n' \
    | grep -P '^MANIFEST_\d{8}_\d{6}\.sha256$' \
    | sed -E 's/^MANIFEST_(.*)\.sha256$/\1/' | sort -r
)
(( ${#CANDIDATES[@]} > 0 )) || fail "aucun lot horaire (MANIFEST_*.sha256) dans $SRC_DIR"

# Le MANIFEST est la source de verite du contenu d'un lot : le nombre de
# fichiers varie (le dump PostgreSQL cmdlib n'est pas toujours produit).
# Un manifeste vide = lot avorte par le timer source ; on l'ecarte et on
# descend au lot suivant, sans jamais toucher aux fichiers sources.
FILE_LIST="$TMP_DIR/files.txt"
: > "$FILE_LIST"
KEEP_TS=()
for ts in "${CANDIDATES[@]}"; do
  (( ${#KEEP_TS[@]} < KEEP )) || break
  man="$SRC_DIR/MANIFEST_${ts}.sha256"
  if [[ ! -s "$man" ]]; then
    log "lot $ts ECARTE : manifeste vide (lot incomplet cote source)"
    continue
  fi
  lot_files=(); ok=1
  while read -r _sum name; do
    [[ -n "${name:-}" ]] || continue
    if [[ ! -f "$SRC_DIR/$name" ]]; then
      log "lot $ts ECARTE : fichier manquant $name"; ok=0; break
    fi
    lot_files+=("$name")
  done < "$man"
  (( ok == 1 && ${#lot_files[@]} > 0 )) || continue
  printf '%s\n' "MANIFEST_${ts}.sha256" "${lot_files[@]}" >> "$FILE_LIST"
  KEEP_TS+=("$ts")
done
(( ${#KEEP_TS[@]} > 0 )) || fail "aucun lot horaire valide"
log "lots retenus (${#KEEP_TS[@]}) : ${KEEP_TS[*]}"
TOTAL_BYTES=$( (cd "$SRC_DIR" && du -cb --files0-from=<(tr '\n' '\0' < "$FILE_LIST") | tail -1 | cut -f1) )
log "volume a miroiter : $(numfmt --to=iec "$TOTAL_BYTES") ($(wc -l < "$FILE_LIST") fichiers)"

# --- 2. transfert bride ---------------------------------------------------
ssh "${SSH_OPTS[@]}" "$REMOTE" "mkdir -p \"\$HOME/$REMOTE_DIR\"" \
  || fail "impossible de creer ~/$REMOTE_DIR sur $REMOTE"

RSYNC_LOG="$TMP_DIR/rsync.log"
log "rsync -> $REMOTE:~/$REMOTE_DIR/"
# Le chemin WAN perd ~2,7% des paquets (mesure du 2026-08-01) et un run dure
# plus de 2 h : une coupure en cours de route est probable. --partial permet de
# reprendre la ou le transfert s'est arrete, --timeout evite un blocage infini.
RSYNC_RC=1
for attempt in 1 2 3; do
  nice -n 19 ionice -c3 rsync -a --partial --stats \
    --bwlimit="$BWLIMIT" \
    --timeout=600 \
    --files-from="$FILE_LIST" \
    --rsync-path="nice -n 19 rsync" \
    -e "ssh ${SSH_OPTS[*]}" \
    "$SRC_DIR/" "$REMOTE:$REMOTE_DIR/" > "$RSYNC_LOG" 2>&1
  RSYNC_RC=$?
  (( RSYNC_RC == 0 )) && break
  log "rsync tentative $attempt echouee (rc=$RSYNC_RC), reprise dans 30s"
  tail -3 "$RSYNC_LOG" | sed 's/^/    /' | tee -a "$LOG_FILE"
  sleep 30
done
sed -n 's/^\(Number of regular files transferred\|Total transferred file size\|Total file size\).*/  &/p' "$RSYNC_LOG" | tee -a "$LOG_FILE"
(( RSYNC_RC == 0 )) || { tail -20 "$RSYNC_LOG" | tee -a "$LOG_FILE"; fail "rsync rc=$RSYNC_RC"; }
XFER_BYTES=$(sed -n 's/^Total transferred file size: \([0-9,]*\) bytes.*/\1/p' "$RSYNC_LOG" | tr -d ',')
log "transfert OK (octets transferes: ${XFER_BYTES:-inconnu})"

# --- 3. rotation distante (strictement confinee a ~/backups-m1) -----------
KEEP_LIST="$(printf '%s\n' "${KEEP_TS[@]}")"
ROT_OUT="$TMP_DIR/rotation.txt"
ssh "${SSH_OPTS[@]}" "$REMOTE" "KEEP='$KEEP_LIST' DIR='$REMOTE_DIR' bash -s" > "$ROT_OUT" 2>&1 <<'REMOTE_ROTATE'
set -uo pipefail
target="$HOME/$DIR"
case "$target" in
  "$HOME"/backups-m1) ;;                       # garde-fou : jamais ailleurs
  *) echo "REFUS: repertoire inattendu $target" >&2; exit 1 ;;
esac
[ -d "$target" ] || { echo "REFUS: $target absent" >&2; exit 1; }
cd "$target" || exit 1
deleted=0
for f in $(ls -1 2>/dev/null); do
  [ -f "$f" ] || continue
  ts=$(printf '%s' "$f" | grep -oE '[0-9]{8}_[0-9]{6}') || true
  if [ -z "${ts:-}" ]; then
    echo "IGNORE (pas d'horodatage): $f"
    continue
  fi
  if printf '%s\n' "$KEEP" | grep -qx "$ts"; then
    continue
  fi
  rm -f -- "./$f" && { echo "SUPPRIME: $f"; deleted=$((deleted+1)); }
done
echo "ROTATION_DELETED=$deleted"
echo "ROTATION_REMAINING_TS=$(ls -1 MANIFEST_*.sha256 2>/dev/null | sed -E 's/^MANIFEST_(.*)\.sha256$/\1/' | sort -r | tr '\n' ' ')"
REMOTE_ROTATE
ROT_RC=$?
grep -E '^(SUPPRIME|IGNORE|ROTATION_|REFUS)' "$ROT_OUT" | sed 's/^/  /' | tee -a "$LOG_FILE"
(( ROT_RC == 0 )) || fail "rotation distante rc=$ROT_RC"

# --- 4. verification d'integrite cote distant -----------------------------
touch "$STATE_FILE"
VERIFY_TS=()
for ts in "${KEEP_TS[@]}"; do
  if (( VERIFY_ALL == 0 )) && grep -qx "$ts" "$STATE_FILE"; then continue; fi
  VERIFY_TS+=("$ts")
done

if (( ${#VERIFY_TS[@]} == 0 )); then
  log "integrite : tous les lots deja verifies (utiliser --verify-all pour forcer)"
else
  log "integrite : recalcul sha256 distant sur ${#VERIFY_TS[@]} lot(s)"
  VER_LIST="$(printf '%s\n' "${VERIFY_TS[@]}")"
  VER_OUT="$TMP_DIR/verify.txt"
  ssh "${SSH_OPTS[@]}" "$REMOTE" "TSL='$VER_LIST' DIR='$REMOTE_DIR' bash -s" > "$VER_OUT" 2>&1 <<'REMOTE_VERIFY'
set -uo pipefail
cd "$HOME/$DIR" || exit 1
rc=0
for ts in $TSL; do
  m="MANIFEST_${ts}.sha256"
  if [ ! -f "$m" ]; then echo "MANQUANT $m"; rc=1; continue; fi
  # nice/ionice : la machine est saturee en permanence
  if out=$(nice -n 19 ionice -c3 sha256sum -c --quiet "$m" 2>&1); then
    echo "OK $ts ($(wc -l < "$m") fichiers)"
  else
    echo "CORROMPU $ts"; echo "$out" | sed 's/^/    /'; rc=1
  fi
done
exit $rc
REMOTE_VERIFY
  VER_RC=$?
  sed 's/^/  /' "$VER_OUT" | tee -a "$LOG_FILE"
  (( VER_RC == 0 )) || fail "verification sha256 distante rc=$VER_RC"
  for ts in "${VERIFY_TS[@]}"; do grep -qx "$ts" "$STATE_FILE" || echo "$ts" >> "$STATE_FILE"; done
  # l'etat ne garde que les lots encore presents
  printf '%s\n' "${KEEP_TS[@]}" | sort > "$TMP_DIR/keep.sorted"
  sort -u "$STATE_FILE" | comm -12 - "$TMP_DIR/keep.sorted" > "$TMP_DIR/state.new" && mv "$TMP_DIR/state.new" "$STATE_FILE"
  log "integrite : ${#VERIFY_TS[@]} lot(s) verifies conformes au MANIFEST"
fi

# --- 5. test de restauration REEL sur M1 depuis la copie distante ---------
if (( SKIP_RESTORE_TEST == 1 )); then
  log "test de restauration ignore (--no-restore-test)"
else
  LATEST_TS="${KEEP_TS[0]}"
  RT_DIR="$TMP_DIR/restore"
  mkdir -p "$RT_DIR"
  DB_GZ="jarvis_master_${LATEST_TS}.db.gz"
  log "restauration : rapatriement de $DB_GZ depuis $REMOTE"
  nice -n 19 rsync -a --bwlimit="$BWLIMIT" -e "ssh ${SSH_OPTS[*]}" \
      "$REMOTE:$REMOTE_DIR/$DB_GZ" "$RT_DIR/" \
    || fail "rapatriement de $DB_GZ impossible"

  gunzip -f "$RT_DIR/$DB_GZ" || fail "decompression de $DB_GZ echouee"
  DB="$RT_DIR/jarvis_master_${LATEST_TS}.db"
  [[ -s "$DB" ]] || fail "base decompressee vide: $DB"
  log "restauration : base decompressee $(numfmt --to=iec "$(stat -c%s "$DB")")"

  INTEG=$(sqlite3 "$DB" 'PRAGMA integrity_check;' 2>&1 | head -5)
  NTAB=$(sqlite3 "$DB" "SELECT count(*) FROM sqlite_master WHERE type='table';" 2>&1)
  log "restauration : integrity_check = ${INTEG}"
  log "restauration : tables = ${NTAB}"

  [[ "$INTEG" == "ok" ]] || fail "integrity_check != ok sur la copie distante"
  [[ "$NTAB" =~ ^[0-9]+$ ]] || fail "comptage des tables illisible: $NTAB"
  (( NTAB > 10 )) || fail "nombre de tables incoherent ($NTAB <= 10)"
  log "restauration VALIDEE depuis la copie distante (lot $LATEST_TS)"
  rm -rf "$RT_DIR"
  log "repertoire temporaire de restauration nettoye"
fi

log "=== miroir termine avec succes ==="
exit 0
