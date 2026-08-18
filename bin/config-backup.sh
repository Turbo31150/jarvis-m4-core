#!/usr/bin/env bash
#
# config-backup.sh — Sauvegarde des CONFIGURATIONS JARVIS (BL1-096)
#
# Sauvegarde les fichiers de config clés en tar.gz horodaté, en EXCLUANT
# strictement tout secret (.env, *.secret*, secrets.db, *.key, *.pem, tokens).
#
# Usage :
#   config-backup.sh                 # backup standard
#   config-backup.sh --dry-run       # liste sans créer l'archive
#   config-backup.sh --from <fichier># liste de chemins/globs surchargeant les défauts
#   config-backup.sh --self-test     # autotest complet avec leurres de secrets
#
set -euo pipefail

# ── Constantes ────────────────────────────────────────────────────────────────
HOME_DIR="${HOME}"
BACKUP_DIR="${CONFIG_BACKUP_DIR:-$HOME_DIR/jarvis/backups/configs}"
LOG_FILE="${CONFIG_BACKUP_LOG:-$HOME_DIR/.local/share/config-backup.log}"
KEEP=10
TS="$(date +%Y%m%d-%H%M%S)"

# Motifs de secrets à EXCLURE et à interdire dans l'archive finale.
# (regex ERE appliquée sur le chemin ; insensible à la casse via grep -iE)
SECRET_REGEX='(^|/)\.env($|\.|/)|\.secret|secrets\.db$|\.key$|\.pem$|(^|/|_|-|\.)(token|tokens|credential|credentials|password|passwd|apikey|api_key)([._-]|$)|id_(rsa|ed25519|ecdsa)(\.pub)?$|\.p12$|\.pfx$'

DRY_RUN=0
SELF_TEST=0
FROM_FILE=""

# ── Logging ───────────────────────────────────────────────────────────────────
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
    printf '%s\n' "$msg" >&2
    mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
    printf '%s\n' "$msg" >> "$LOG_FILE" 2>/dev/null || true
}
fail() { log "FAIL: $*"; exit 1; }

# ── Parsing arguments ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)   DRY_RUN=1; shift ;;
        --self-test) SELF_TEST=1; shift ;;
        --from)      FROM_FILE="${2:-}"; shift 2 ;;
        -h|--help)
            grep '^#' "$0" | sed 's/^# \{0,1\}//' | head -n 20
            exit 0 ;;
        *) fail "Argument inconnu : $1" ;;
    esac
done

# ── Liste des chemins/globs de config par défaut ──────────────────────────────
default_sources() {
    cat <<EOF
$HOME_DIR/.config/systemd/user/*.service
$HOME_DIR/.config/systemd/user/*.timer
$HOME_DIR/.claude/settings.json
$HOME_DIR/.claude/settings.local.json
$HOME_DIR/.claude/.mcp.json
$HOME_DIR/jarvis/*.json
$HOME_DIR/labo/bibliotheque/lib/*.tsv
EOF
}

# Résout une liste de globs en fichiers réels existants, EXCLUANT les secrets.
# Écrit la liste sur stdout (un chemin par ligne). Set de retour :
#   0 = au moins un fichier ; 1 = aucun fichier.
resolve_sources() {
    local src_lines file
    if [[ -n "$FROM_FILE" ]]; then
        [[ -f "$FROM_FILE" ]] || fail "Fichier --from introuvable : $FROM_FILE"
        src_lines="$(grep -vE '^\s*(#|$)' "$FROM_FILE" || true)"
    else
        src_lines="$(default_sources)"
    fi

    local -a resolved=()
    while IFS= read -r pattern; do
        [[ -z "$pattern" ]] && continue
        # Expansion du glob (nullglob local)
        local matches=()
        shopt -s nullglob
        # shellcheck disable=SC2206
        matches=( $pattern )
        shopt -u nullglob
        for file in "${matches[@]}"; do
            [[ -f "$file" ]] || continue
            # Exclusion stricte des secrets
            if printf '%s' "$file" | grep -qiE "$SECRET_REGEX"; then
                log "EXCLU (secret) : $file"
                continue
            fi
            resolved+=( "$file" )
        done
    done <<< "$src_lines"

    # Dédup en préservant l'ordre
    if [[ ${#resolved[@]} -gt 0 ]]; then
        printf '%s\n' "${resolved[@]}" | awk '!seen[$0]++'
        return 0
    fi
    return 1
}

# Vérifie qu'aucun secret n'est présent dans une archive donnée.
# Retourne 0 si propre, 1 si un secret est détecté.
verify_no_secrets() {
    local archive="$1" bad
    bad="$(tar -tzf "$archive" | grep -iE "$SECRET_REGEX" || true)"
    if [[ -n "$bad" ]]; then
        log "SECRET DÉTECTÉ dans l'archive :"
        printf '%s\n' "$bad" | while IFS= read -r l; do log "  -> $l"; done
        return 1
    fi
    return 0
}

# ── Rotation : garder les KEEP dernières archives ─────────────────────────────
rotate() {
    local -a archives
    mapfile -t archives < <(ls -1t "$BACKUP_DIR"/configs-*.tar.gz 2>/dev/null || true)
    local n=${#archives[@]}
    if (( n > KEEP )); then
        local i
        for (( i=KEEP; i<n; i++ )); do
            rm -f "${archives[$i]}" "${archives[$i]}.sha256"
            log "Rotation : suppression $(basename "${archives[$i]}")"
        done
    fi
}

# ── Backup principal ──────────────────────────────────────────────────────────
do_backup() {
    local files_list
    if ! files_list="$(resolve_sources)"; then
        fail "Aucun fichier de config trouvé à sauvegarder."
    fi

    local count
    count="$(printf '%s\n' "$files_list" | grep -c . || true)"

    if (( DRY_RUN == 1 )); then
        log "DRY-RUN : $count fichier(s) seraient inclus :"
        printf '%s\n' "$files_list" | while IFS= read -r f; do
            [[ -n "$f" ]] && log "  + $f"
        done
        log "DRY-RUN : archive NON créée."
        return 0
    fi

    mkdir -p "$BACKUP_DIR"
    local archive="$BACKUP_DIR/configs-$TS.tar.gz"

    # Liste des chemins pour tar via fichier temporaire (gère espaces/caractères)
    local list_tmp
    list_tmp="$(mktemp)"
    trap 'rm -f "$list_tmp"' RETURN
    printf '%s\n' "$files_list" | grep . > "$list_tmp"

    # Création de l'archive (chemins absolus -> tar retire le / initial).
    tar -czf "$archive" --files-from="$list_tmp" 2>/dev/null

    # Vérification post-création : AUCUN secret ne doit être présent.
    if ! verify_no_secrets "$archive"; then
        rm -f "$archive"
        fail "Secret détecté dans l'archive -> archive supprimée."
    fi

    # Manifest sha256
    ( cd "$BACKUP_DIR" && sha256sum "$(basename "$archive")" > "$(basename "$archive").sha256" )

    rotate

    local size
    size="$(du -h "$archive" | cut -f1)"
    log "OK : $archive ($size, $count fichier(s))"
    log "SHA256 : $(cut -d' ' -f1 < "$archive.sha256")"
}

# ── Self-test ─────────────────────────────────────────────────────────────────
run_self_test() {
    local tmproot bkp orig_backup_dir orig_from
    tmproot="$(mktemp -d)"
    log "SELFTEST : arbre temporaire $tmproot"

    # Arbre de config leurre
    mkdir -p "$tmproot/conf" "$tmproot/dest"
    # Fichiers de config LÉGITIMES
    printf '{"name":"jarvis"}\n'        > "$tmproot/conf/settings.json"
    printf 'a\tb\tc\n1\t2\t3\n'          > "$tmproot/conf/index.tsv"
    printf '[Unit]\nDescription=x\n'     > "$tmproot/conf/demo.service"
    # LEURRES de secrets (doivent être EXCLUS)
    printf 'API_TOKEN=deadbeef\n'        > "$tmproot/conf/.env"
    printf 'SECRETKEY=1234\n'            > "$tmproot/conf/api.key"
    printf 'PRIV\n'                      > "$tmproot/conf/server.pem"
    printf 'x\n'                         > "$tmproot/conf/prod.secret.json"

    # Fichier --from ciblant tout le dossier conf
    local fromf="$tmproot/from.list"
    { printf '%s\n' "$tmproot/conf/*"; printf '%s\n' "$tmproot/conf/.env"; } > "$fromf"

    # Exécuter un backup isolé (sous-shell avec env surchargé)
    bkp="$tmproot/dest"
    local out rc=0
    out="$(
        CONFIG_BACKUP_DIR="$bkp" \
        CONFIG_BACKUP_LOG="$tmproot/selftest.log" \
        bash "$0" --from "$fromf" 2>&1
    )" || rc=$?
    printf '%s\n' "$out" | sed 's/^/    [inner] /'
    (( rc == 0 )) || { rm -rf "$tmproot"; fail "SELFTEST : backup interne a échoué (rc=$rc)"; }

    # Localiser l'archive produite
    local archive
    archive="$(ls -1t "$bkp"/configs-*.tar.gz 2>/dev/null | head -n1 || true)"
    [[ -n "$archive" && -f "$archive" ]] || { rm -rf "$tmproot"; fail "SELFTEST : archive non produite"; }

    # 1) sha256 valide
    ( cd "$bkp" && sha256sum -c "$(basename "$archive").sha256" >/dev/null ) \
        || { rm -rf "$tmproot"; fail "SELFTEST : sha256 invalide"; }
    log "SELFTEST : sha256 OK"

    # 2) contenu de l'archive
    local contents
    contents="$(tar -tzf "$archive")"

    # 3) secrets ABSENTS
    local leaked
    leaked="$(printf '%s\n' "$contents" | grep -iE '\.env$|api\.key$|\.pem$|\.secret' || true)"
    if [[ -n "$leaked" ]]; then
        rm -rf "$tmproot"
        fail "SELFTEST : SECRET PRÉSENT dans l'archive : $leaked"
    fi
    log "SELFTEST : secrets ABSENTS (OK)"

    # 4) config légitime PRÉSENTE
    printf '%s\n' "$contents" | grep -q 'settings\.json$' \
        || { rm -rf "$tmproot"; fail "SELFTEST : config légitime settings.json manquante"; }
    printf '%s\n' "$contents" | grep -q 'index\.tsv$' \
        || { rm -rf "$tmproot"; fail "SELFTEST : config légitime index.tsv manquante"; }
    printf '%s\n' "$contents" | grep -q 'demo\.service$' \
        || { rm -rf "$tmproot"; fail "SELFTEST : config légitime demo.service manquante"; }
    log "SELFTEST : configs légitimes PRÉSENTES (OK)"

    # Nettoyage
    rm -rf "$tmproot"
    log "SELFTEST OK"
    exit 0
}

# ── Point d'entrée ────────────────────────────────────────────────────────────
if (( SELF_TEST == 1 )); then
    run_self_test
else
    do_backup
fi
