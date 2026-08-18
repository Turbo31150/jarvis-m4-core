#!/usr/bin/env bash
# sauvegarde-m4-complete.sh — Protocole SAUVEGARDE M4 : SQLite3 + PostgreSQL + manifeste.
#
# Cible : disque M1 (180 Go libres) et NON la racine / (89 % pleine, 39 Go de
# backups déjà là).
#
# Deux pièges corrigés au banc le 2026-08-18 (un premier run les a révélés) :
#  1. ratisser ~/jarvis en aveugle embarque ~/jarvis/backups/ — 39 Go de
#     sauvegardes de sauvegardes, dont des jarvis_master.db périmés de 45 Mo.
#     On ne sauvegarde QUE les bases vivantes.
#  2. nommer la sortie par basename fait entrer en collision les homonymes
#     (jarvis_master.db existe en 6 exemplaires) : le dernier écrase les autres
#     et le .gz de 7,9 Mo fait croire à une sauvegarde de la base de 6,5 Go.
#     La sortie porte désormais le chemin relatif aplati.
set -uo pipefail

TS="$(date +%Y%m%d_%H%M%S)"
DEST="${SAUV_DEST:-/media/pamerys/JARVIS-M1/storage-offload/sauvegardes-m4}/$TS"
mkdir -p "$DEST"
MANIFEST="$DEST/MANIFEST.sha256"
LOG="$DEST/sauvegarde.log"
: > "$MANIFEST"
JDOCKER="$HOME/jarvis/bin/jarvis-docker"

log(){ echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }
log "=== SAUVEGARDE M4 — $TS → $DEST ==="
ok=0; ko=0

# ---------- 1. SQLite3 — bases VIVANTES uniquement ----------
# ~/jarvis/*.db sont des liens vers ~/jarvis/databases/ : la dédup par inode
# garantit qu'on ne dumpe pas deux fois les 6,5 Go de jarvis_master.
CANDIDATS=()
for d in "$HOME/jarvis/databases" "$HOME/jarvis/data" "$HOME/jarvis" "$HOME/jarvis/board" "$HOME/jarvis/logs"; do
  while IFS= read -r f; do CANDIDATS+=("$f"); done \
    < <(find "$d" -maxdepth 1 -name '*.db' ! -name '*.bak*' 2>/dev/null | sort)
done

declare -A seen
for db in "${CANDIDATS[@]}"; do
  real="$(readlink -f "$db")"
  [ -f "$real" ] || continue
  case "$real" in *"/jarvis/backups/"*) continue ;; esac
  key="$(stat -c '%d:%i' "$real")"
  [ -n "${seen[$key]:-}" ] && continue
  seen[$key]=1
  # nom = chemin relatif à ~/jarvis, aplati → aucune collision d'homonymes
  rel="${real#$HOME/jarvis/}"; rel="${rel//\//_}"; rel="${rel%.db}"
  out="$DEST/${rel}.db"
  log "SQLite $rel ($(du -h "$real" | cut -f1)) …"
  if sqlite3 "$real" "VACUUM INTO '$out'" 2>>"$LOG"; then
    gzip -1 -f "$out"
    sha256sum "${out}.gz" | sed "s| .*/| |" >> "$MANIFEST"
    log "  ok → ${rel}.db.gz ($(du -h "${out}.gz" | cut -f1))"
    ok=$((ok+1))
  else
    log "  ÉCHEC VACUUM : $real"; rm -f "$out"; ko=$((ko+1))
  fi
done

# ---------- 2. PostgreSQL — pile réelle (jarvis-docker, pas docker local) ----------
for c in jarvis-postgres jarvis-pg-biblio; do
  if "$JDOCKER" ps --format '{{.Names}}' 2>/dev/null | grep -qx "$c"; then
    out="$DEST/pg_${c}.sql.gz"
    log "pg_dumpall $c …"
    if "$JDOCKER" exec "$c" pg_dumpall -U jarvis 2>>"$LOG" | gzip -1 > "$out" && [ -s "$out" ]; then
      sha256sum "$out" | sed "s| .*/| |" >> "$MANIFEST"
      log "  ok → pg_${c}.sql.gz ($(du -h "$out" | cut -f1))"
      ok=$((ok+1))
    else
      log "  ÉCHEC pg_dumpall : $c"; rm -f "$out"; ko=$((ko+1))
    fi
  else
    log "skip $c (absent)"
  fi
done

# ---------- 3. Config critique (les secrets restent hors archive) ----------
tar czf "$DEST/config-jarvis.tar.gz" -C "$HOME" \
  .claude/CLAUDE.md .claude/rules .claude/agents .mcp.json jarvis/CLAUDE.md 2>/dev/null
if [ -s "$DEST/config-jarvis.tar.gz" ]; then
  sha256sum "$DEST/config-jarvis.tar.gz" | sed "s| .*/| |" >> "$MANIFEST"
  log "ok → config-jarvis.tar.gz"; ok=$((ok+1))
fi

log "=== TERMINÉ : $ok artefact(s), $ko échec(s) — $(du -sh "$DEST" | cut -f1) ==="
echo "$DEST" > /tmp/derniere-sauvegarde-m4.path
