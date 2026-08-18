#!/usr/bin/env bash
#
# openclaw-backup.sh — Backup horodaté tar.gz de ~/.openclaw (BL1-012)
#
# Contraintes :
#   - Archive : ~/jarvis/backups/openclaw/openclaw-<YYYYMMDD-HHMMSS>.tar.gz
#   - Exclut les secrets (.env, *.secret*, secrets.db, *.key, *.pem, node_modules, .git, caches)
#   - Rotation : ne conserve que les 7 dernières archives
#   - Source en lecture seule, jamais modifiée
#   - Manifest .sha256 à côté de chaque archive
#   - --dry-run : simule sans créer (défaut si source absente -> exit 0)
#   - --self-test : test complet auto-nettoyé -> "SELFTEST OK"
#   - Log : ~/.local/share/openclaw-backup.log
#
set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
: "${HOME:?HOME non defini}"

SRC_DIR="${OPENCLAW_SRC:-$HOME/.openclaw}"
DEST_DIR="${OPENCLAW_BACKUP_DIR:-$HOME/jarvis/backups/openclaw}"
LOG_FILE="${OPENCLAW_BACKUP_LOG:-$HOME/.local/share/openclaw-backup.log}"
KEEP=7
PREFIX="openclaw"

# Motifs d'exclusion (secrets + bruit). Appliques via --exclude de tar.
EXCLUDES=(
  "--exclude=.env"
  "--exclude=.env.*"
  "--exclude=*.env"
  "--exclude=*.secret*"
  "--exclude=secrets.db"
  "--exclude=*.key"
  "--exclude=*.pem"
  "--exclude=node_modules"
  "--exclude=.git"
  "--exclude=.cache"
  "--exclude=*/cache"
  "--exclude=*.tmp"
)

# ---------------------------------------------------------------------------
# Journalisation
# ---------------------------------------------------------------------------
log() {
  local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
  mkdir -p "$(dirname "$LOG_FILE")"
  printf '%s\n' "$msg" | tee -a "$LOG_FILE"
}

# ---------------------------------------------------------------------------
# Rotation : conserver les $KEEP archives les plus recentes
# ---------------------------------------------------------------------------
rotate() {
  local dir="$1"
  local -a archives
  # Tri par date (plus recent d'abord) via nom horodate.
  mapfile -t archives < <(ls -1 "$dir"/${PREFIX}-*.tar.gz 2>/dev/null | sort -r || true)
  local count="${#archives[@]}"
  if (( count > KEEP )); then
    local i
    for (( i = KEEP; i < count; i++ )); do
      local old="${archives[$i]}"
      rm -f -- "$old" "${old}.sha256"
      log "ROTATION supprime : $(basename "$old")"
    done
  fi
}

# ---------------------------------------------------------------------------
# Backup principal
# ---------------------------------------------------------------------------
do_backup() {
  local src="$1" dest_dir="$2" dry="$3"
  local stamp archive sha

  if [[ ! -d "$src" ]]; then
    log "SOURCE absente : $src -> rien a faire (exit 0)"
    return 0
  fi

  stamp="$(date '+%Y%m%d-%H%M%S')"
  archive="$dest_dir/${PREFIX}-${stamp}.tar.gz"

  mkdir -p "$dest_dir"

  if [[ "$dry" == "1" ]]; then
    log "DRY-RUN : creerait $archive"
    log "DRY-RUN : exclusions = ${EXCLUDES[*]}"
    # Aperçu (liste seulement, aucune ecriture).
    tar "${EXCLUDES[@]}" -C "$(dirname "$src")" -cvf /dev/null "$(basename "$src")" \
      2>/dev/null | head -n 20 | sed 's/^/DRY-RUN   inclus: /' | tee -a "$LOG_FILE" || true
    log "DRY-RUN : rotation garderait les $KEEP plus recentes"
    return 0
  fi

  log "BACKUP debut : $src -> $archive"
  # -C parent + basename : archive relative, source jamais modifiee (lecture seule).
  tar "${EXCLUDES[@]}" -C "$(dirname "$src")" -czf "$archive" "$(basename "$src")"

  # Manifest sha256
  sha="$(sha256sum "$archive" | awk '{print $1}')"
  printf '%s  %s\n' "$sha" "$(basename "$archive")" > "${archive}.sha256"
  log "BACKUP ok : $(basename "$archive") ($(du -h "$archive" | cut -f1)) sha256=$sha"

  rotate "$dest_dir"
  return 0
}

# ---------------------------------------------------------------------------
# Self-test intégré
# ---------------------------------------------------------------------------

# Corps du self-test : opere dans le dossier temporaire fourni en argument.
_self_test_body() {
  local tmp="$1"
  local src dest archive sha_file recomputed listing

  src="$tmp/.openclaw"
  dest="$tmp/backups"
  mkdir -p "$src/sub" "$src/node_modules" "$src/.git"

  # Contenu legitime.
  echo "config normale" > "$src/config.json"
  echo "data" > "$src/sub/data.txt"
  # Secrets qui DOIVENT etre exclus.
  echo "SECRET=42" > "$src/.env"
  echo "API=zzz"   > "$src/prod.env"
  echo "sk-xxx"    > "$src/api.key"
  echo "cert"      > "$src/server.pem"
  echo "top"       > "$src/my.secret.txt"
  : > "$src/secrets.db"
  echo "junk"      > "$src/node_modules/pkg.js"
  echo "gitobj"    > "$src/.git/HEAD"

  # Lance le backup dans l'environnement de test.
  OPENCLAW_SRC="$src" OPENCLAW_BACKUP_DIR="$dest" OPENCLAW_BACKUP_LOG="$tmp/test.log" \
    do_backup "$src" "$dest" "0"

  # 1. archive existe
  archive="$(ls -1 "$dest"/${PREFIX}-*.tar.gz 2>/dev/null | head -n1 || true)"
  if [[ -z "$archive" || ! -f "$archive" ]]; then
    echo "SELFTEST FAIL : archive introuvable"; return 1
  fi

  # 2. sha256 present et valide
  sha_file="${archive}.sha256"
  if [[ ! -f "$sha_file" ]]; then
    echo "SELFTEST FAIL : manifest .sha256 absent"; return 1
  fi
  recomputed="$(sha256sum "$archive" | awk '{print $1}')"
  if [[ "$recomputed" != "$(awk '{print $1}' "$sha_file")" ]]; then
    echo "SELFTEST FAIL : sha256 invalide"; return 1
  fi

  # 3. secrets exclus, contenu legitime present
  listing="$(tar -tzf "$archive")"
  if echo "$listing" | grep -Eq '(\.env|prod\.env|api\.key|server\.pem|my\.secret\.txt|secrets\.db|node_modules|\.git/)'; then
    echo "SELFTEST FAIL : un secret/exclu est present dans l'archive :"
    echo "$listing" | grep -E '(\.env|prod\.env|api\.key|server\.pem|my\.secret\.txt|secrets\.db|node_modules|\.git/)'
    return 1
  fi
  if ! echo "$listing" | grep -q 'config.json'; then
    echo "SELFTEST FAIL : contenu legitime (config.json) manquant"; return 1
  fi

  # 4. source intacte (lecture seule)
  if [[ ! -f "$src/.env" || ! -f "$src/config.json" ]]; then
    echo "SELFTEST FAIL : source modifiee"; return 1
  fi

  echo "SELFTEST OK"
  return 0
}

# Enveloppe : cree le tmp, execute le corps, nettoie TOUJOURS, propage le code.
self_test() {
  local tmp rc=0
  tmp="$(mktemp -d "${TMPDIR:-/tmp}/openclaw-selftest.XXXXXX")"
  _self_test_body "$tmp" || rc=$?
  rm -rf "$tmp"
  return "$rc"
}

# ---------------------------------------------------------------------------
# Aide
# ---------------------------------------------------------------------------
usage() {
  cat <<EOF
openclaw-backup.sh — backup tar.gz de ~/.openclaw

Usage :
  openclaw-backup.sh            Effectue le backup (rotation 7)
  openclaw-backup.sh --dry-run  Simule sans rien ecrire
  openclaw-backup.sh --self-test  Test integre auto-nettoye
  openclaw-backup.sh --help     Cette aide

Source  : $SRC_DIR
Dest    : $DEST_DIR
Log     : $LOG_FILE
Conserve: $KEEP dernieres archives
EOF
}

# ---------------------------------------------------------------------------
# Entree
# ---------------------------------------------------------------------------
main() {
  local mode="run"
  case "${1:-}" in
    --dry-run)   mode="dry" ;;
    --self-test) mode="selftest" ;;
    --help|-h)   usage; exit 0 ;;
    "")          mode="run" ;;
    *) echo "Option inconnue : $1" >&2; usage; exit 2 ;;
  esac

  case "$mode" in
    selftest) self_test ;;
    dry)      do_backup "$SRC_DIR" "$DEST_DIR" "1" ;;
    run)
      # Defaut sur --dry-run si la source est absente (exit 0 propre).
      if [[ ! -d "$SRC_DIR" ]]; then
        log "SOURCE absente : $SRC_DIR -> bascule en dry-run, exit 0"
        do_backup "$SRC_DIR" "$DEST_DIR" "1"
      else
        do_backup "$SRC_DIR" "$DEST_DIR" "0"
      fi
      ;;
  esac
}

main "$@"
