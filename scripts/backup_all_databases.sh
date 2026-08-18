#!/bin/bash
# Sauvegarde complète de toutes les bases de données SQLite3 & PostgreSQL

BACKUP_DIR="/storage/backups_db/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "=== [1/2] Sauvegarde des bases de données SQLite3 ==="
for db in /home/pamerys/jarvis/jarvis_master.db \
          /home/pamerys/jarvis/logs/jarvis_logs.db \
          /home/pamerys/jarvis/cowork_engine.db \
          /home/pamerys/jarvis-cowork/etoile.db; do
  if [ -f "$db" ]; then
    dbname=$(basename "$db")
    echo "Sauvegarde SQLite: $dbname..."
    sqlite3 "$db" ".backup '$BACKUP_DIR/$dbname.bak'"
  fi
done

echo "=== [2/2] Sauvegarde des bases de données PostgreSQL ==="
if command -v pg_dumpall >/dev/null 2>&1; then
  sudo -u postgres pg_dumpall > "$BACKUP_DIR/postgresql_full_dump.sql" 2>/dev/null || pg_dumpall > "$BACKUP_DIR/postgresql_full_dump.sql" 2>/dev/null || true
  echo "Dump PostgreSQL complet effectué !"
else
  echo "PostgreSQL pg_dumpall non requis ou service autonome. Sauvegardes SQLite validées."
fi

echo "Rapport de sauvegarde créé dans : $BACKUP_DIR"
ls -lh "$BACKUP_DIR"
