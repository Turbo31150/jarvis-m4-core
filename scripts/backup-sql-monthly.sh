#!/usr/bin/env bash
# Backup mensuel SQL : Postgres host + Docker + SQLite + /tmp/BASE-SQL3
# Cron: 0 3 1 * * (1er du mois à 3h)
set -euo pipefail

TS=$(date +%Y%m%d_%H%M%S)
BACKUP=/home/pamerys/jarvis/backups/sql/$TS
mkdir -p "$BACKUP/postgres_host" "$BACKUP/postgres_docker" "$BACKUP/sqlite" "$BACKUP/tmp_BASE-SQL3"

sudo -n -u postgres pg_dumpall 2>/dev/null | gzip > "$BACKUP/postgres_host/pg_dumpall_${TS}.sql.gz" || true
for DB in jarvis jarvis_pg; do
  sudo -n -u postgres pg_dump "$DB" 2>/dev/null | gzip > "$BACKUP/postgres_host/host_${DB}_${TS}.sql.gz" || true
done

PG_CONTAINER=$(docker ps --filter "name=jarvis_prod_postgres" --format "{{.ID}}" 2>/dev/null | head -1)
[ -n "$PG_CONTAINER" ] && docker exec "$PG_CONTAINER" pg_dump -U jarvis -d jarvis 2>/dev/null | gzip > "$BACKUP/postgres_docker/docker_jarvis_${TS}.sql.gz"

for DB in /home/pamerys/jarvis/jarvis_master.db /home/pamerys/jarvis/secrets.db /home/pamerys/jarvis/cowork_engine.db /home/pamerys/jarvis/jarvis_logs.db /home/pamerys/jarvis/data/etoile.db /home/pamerys/jarvis/data/jarvis.db /home/pamerys/jarvis/data/scheduler.db /home/pamerys/jarvis/data/linkedin_history.sqlite /home/pamerys/jarvis/logs/bench_results.db /home/pamerys/jarvis/logs/jarvis_logs.db; do
  [ -f "$DB" ] || continue
  NAME=$(basename "$DB"); DIR=$(dirname "$DB" | sed 's|/home/pamerys/jarvis/||' | tr / _ )
  sqlite3 "$DB" ".backup '$BACKUP/sqlite/${DIR}_${NAME}'" 2>/dev/null && gzip "$BACKUP/sqlite/${DIR}_${NAME}"
done

[ -d /tmp/BASE-SQL3 ] && tar -czf "$BACKUP/tmp_BASE-SQL3/BASE-SQL3_${TS}.tar.gz" -C /tmp BASE-SQL3 2>/dev/null

du -sh "$BACKUP" | tee "$BACKUP/MANIFEST.txt"
ls -1dt /home/pamerys/jarvis/backups/sql/*/ 2>/dev/null | tail -n +7 | xargs rm -rf 2>/dev/null || true
logger -t jarvis-backup "Backup SQL OK: $BACKUP ($(du -sh "$BACKUP" | cut -f1))"
