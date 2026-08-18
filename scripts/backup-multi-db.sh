#!/usr/bin/env bash
# backup-multi-db.sh — Réplication LOCALE fréquente (horaire) des DBs critiques M1.
# Complète le backup quotidien GitHub LFS (backup-sql-github.sh) pour minimiser la
# perte de données entre 2 backups, sans dépendre de M5 (DOWN longue durée).
# Phase 1.2 roadmap — snapshot atomique SQLite + pg_dump cmdlib, rotation, manifest.
set -euo pipefail

JARVIS_DIR="${JARVIS_DIR:-/home/pamerys/jarvis}"
DEST="${HOURLY_BACKUP_DIR:-$JARVIS_DIR/backups/hourly}"
KEEP="${KEEP_PER_DB:-24}"          # nb de snapshots conservés par base
TS="$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DEST"

# --- Verrou : un seul run à la fois (chevauchement timer/relance manuelle) ---
exec 9>"$DEST/.lock"
flock -n 9 || { echo "run déjà en cours, abandon"; exit 0; }

# DBs SQLite critiques (chemins absolus réels ; chaque absente est skippée proprement)
SQLITE_DBS=(
  "$JARVIS_DIR/jarvis_master.db"   # 154M — tasks, routing, repos index (la plus critique)
  "$JARVIS_DIR/cowork_engine.db"   # 34M  — état agents OpenClaw
  "$JARVIS_DIR/data/jarvis.db"     # 8M   — base opérationnelle principale
  "$JARVIS_DIR/data/etoile.db"     # 1.3M — analytics/contenu
  "$JARVIS_DIR/data/scheduler.db"  # cron jobs
)

# Container PostgreSQL « bibliothèque »
# Détection dynamique du container Postgres (les noms changent au gré des réorgs :
# ex. commande_directe_bibliotheque-db-1 → jv-infra-pg-biblio). Override par PG_CONTAINER.
PG_CONTAINER="${PG_CONTAINER:-$(docker ps --format '{{.Names}} {{.Image}}' 2>/dev/null | awk '/postgres/{print $1; exit}')}"
PG_CONTAINER="${PG_CONTAINER:-jv-infra-pg-biblio}"
PG_USER="${PG_USER:-cmduser}"
PG_DB="${PG_DB:-cmdlib}"

MANIFEST="$DEST/MANIFEST_${TS}.sha256"
: > "$MANIFEST"
produced=0

# --- Piège de sortie : un run interrompu ne laisse ni .db non compressé ni
# manifeste vide trompeur. Ne touche jamais aux .gz déjà produits (ce run ou un
# lot antérieur) : le glob est restreint au timestamp du run courant.
cleanup() {
  rm -f "$DEST"/*_"${TS}".db "$DEST"/*_"${TS}".db-journal
  [ -s "$MANIFEST" ] || rm -f "$MANIFEST"
}
trap cleanup EXIT INT TERM

log() { echo "[backup-multi-db $(date +%H:%M:%S)] $*"; }

# --- SQLite : snapshot atomique WAL-safe via VACUUM INTO (jamais cp à chaud) ---
# VACUUM INTO plutôt que .backup : l'API .backup redémarre la copie à chaque
# écriture concurrente et diverge sur une base écrite en continu (jarvis_master :
# un run avait tourné 7 h sans converger). VACUUM INTO lit dans UNE transaction
# et converge toujours. Contrainte : il refuse d'écrire sur une cible existante.
for db in "${SQLITE_DBS[@]}"; do
  if [ ! -f "$db" ]; then
    log "skip (absent) : $db"
    continue
  fi
  name="$(basename "$db" .db)"
  out="$DEST/${name}_${TS}.db"
  rm -f "$out"
  if sqlite3 "$db" "VACUUM INTO '$out'" 2>/dev/null; then
    gzip -f "$out"
    sha256sum "${out}.gz" | sed "s| .*/| |" >> "$MANIFEST"
    log "ok : ${name}_${TS}.db.gz ($(du -h "${out}.gz" | cut -f1))"
    produced=$((produced+1))
  else
    log "ÉCHEC dump : $db"
    rm -f "$out"
  fi
done

# --- PostgreSQL cmdlib (skip propre si container down) ---
if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$PG_CONTAINER"; then
  pgout="$DEST/${PG_DB}_${TS}.sql.gz"
  if docker exec "$PG_CONTAINER" pg_dump -U "$PG_USER" "$PG_DB" 2>/dev/null | gzip > "$pgout"; then
    if [ -s "$pgout" ]; then
      sha256sum "$pgout" | sed "s| .*/| |" >> "$MANIFEST"
      log "ok : ${PG_DB}_${TS}.sql.gz ($(du -h "$pgout" | cut -f1))"
      produced=$((produced+1))
    else
      log "ÉCHEC pg_dump (vide) : $PG_DB"; rm -f "$pgout"
    fi
  else
    log "ÉCHEC pg_dump : $PG_DB"; rm -f "$pgout"
  fi
else
  log "skip Postgres (container $PG_CONTAINER absent)"
fi

# --- Rotation : garder les $KEEP derniers par base ---
# Le glob ${name}_[0-9]* évite que "jarvis" capture "jarvis_master" (le _<chiffre> du
# timestamp distingue jarvis_2026… de jarvis_master_2026…).
for name in jarvis_master cowork_engine jarvis etoile scheduler "$PG_DB"; do
  mapfile -t old < <(ls -1t "$DEST/${name}_"[0-9]*.gz 2>/dev/null | tail -n +$((KEEP+1)))
  for f in "${old[@]}"; do rm -f "$f"; log "rotation : $(basename "$f")"; done
done

log "terminé — $produced base(s) snapshot, manifest=$(basename "$MANIFEST")"
[ "$produced" -gt 0 ] || { log "AUCUNE base sauvegardée"; exit 1; }
