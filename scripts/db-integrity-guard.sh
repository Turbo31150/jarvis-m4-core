#!/bin/bash
# db-integrity-guard.sh — Garde d'intégrité des bases SQLite critiques JARVIS.
#
# Pourquoi : en juin 2026, data/jarvis.db a accumulé une corruption d'index
# (table containers, PK désenforcée après reboots GPU non propres) qui s'est
# propagée silencieusement dans TOUS les backups pendant 10 jours, car aucun
# script de backup ne vérifiait l'intégrité avant d'archiver.
#
# Ce garde tourne AVANT la fenêtre de backup (cron 1h, backups à 2-5h) :
#   - PRAGMA integrity_check sur chaque base critique
#   - si KO : alerte (log + Telegram si dispo) + marqueur .CORRUPT
#     → les scripts de backup peuvent tester ce marqueur et refuser d'archiver
#   - réparation auto optionnelle (--repair) via dump→reload dédupliqué
#
# Usage:
#   bash db-integrity-guard.sh            # check + alerte seulement (sûr)
#   bash db-integrity-guard.sh --repair   # check + répare les bases corrompues
set -uo pipefail

CRITICAL_DBS=(
  "/home/pamerys/jarvis/data/jarvis.db"
  "/home/pamerys/jarvis/data/etoile.db"
  "/home/pamerys/jarvis/jarvis_master.db"
  "/home/pamerys/jarvis/cowork_engine.db"
)

LOG="/home/pamerys/jarvis/logs/db-integrity-guard.log"
mkdir -p "$(dirname "$LOG")"
REPAIR=0
[ "${1:-}" = "--repair" ] && REPAIR=1
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

log() { echo "[$TS] $*" | tee -a "$LOG"; }

alert() {
  local msg="$1"
  log "ALERT: $msg"
  # Telegram best-effort (ne bloque jamais)
  local notif="/home/pamerys/jarvis/scripts/notify-telegram.sh"
  [ -x "$notif" ] && "$notif" "🔴 DB-GUARD: $msg" >/dev/null 2>&1 || true
}

repair_db() {
  # Réparation non destructive : dump → reload (dédup containers) → swap atomique.
  local db="$1"
  local tmp_sql="/tmp/dbguard_$(basename "$db").sql"
  local tmp_db="/tmp/dbguard_$(basename "$db").repaired"
  local backup="${db}.corrupt-$(date +%Y%m%d_%H%M%S)"

  log "REPAIR start: $db"
  cp "$db" "$backup" || { alert "repair abort: backup brut échoué $db"; return 1; }

  if ! sqlite3 "$db" ".dump" > "$tmp_sql" 2>/dev/null; then
    alert "repair abort: dump illisible $db (corruption profonde — restore manuel requis)"
    return 1
  fi
  # Dédup défensive sur la table containers (cause connue) si présente
  sed -E 's/^INSERT INTO "?containers"? VALUES/INSERT OR IGNORE INTO containers VALUES/' "$tmp_sql" > "${tmp_sql}.dedup"

  rm -f "$tmp_db"
  if ! sqlite3 "$tmp_db" < "${tmp_sql}.dedup" 2>/dev/null; then
    alert "repair abort: reload échoué $db"
    return 1
  fi
  if [ "$(sqlite3 "$tmp_db" 'PRAGMA integrity_check;' 2>&1 | head -1)" != "ok" ]; then
    alert "repair abort: base reconstruite toujours KO $db"
    return 1
  fi

  # Swap atomique (suppr WAL/SHM stale, copie same-fs, rename)
  local staging="${db}.repaired.staging"
  cp "$tmp_db" "$staging"
  rm -f "${db}-wal" "${db}-shm"
  mv -f "$staging" "$db"
  sqlite3 "$db" "PRAGMA journal_mode=WAL; ANALYZE;" >/dev/null 2>&1
  log "REPAIR OK: $db (original corrompu conservé → $backup)"
  alert "réparé automatiquement: $(basename "$db") (backup: $(basename "$backup"))"
  return 0
}

RC=0
for db in "${CRITICAL_DBS[@]}"; do
  [ -f "$db" ] || { log "SKIP absent: $db"; continue; }
  res="$(sqlite3 "$db" 'PRAGMA integrity_check;' 2>&1 | head -1)"
  if [ "$res" = "ok" ]; then
    log "OK: $db"
    rm -f "${db}.CORRUPT"
  else
    RC=1
    touch "${db}.CORRUPT"
    alert "INTÉGRITÉ KO: $db → $res"
    if [ "$REPAIR" = "1" ]; then
      if repair_db "$db"; then
        rm -f "${db}.CORRUPT"
        RC=0
      fi
    fi
  fi
done

log "Guard terminé (rc=$RC)"
exit $RC
