#!/bin/bash
# backup-sql-github.sh — Backup SQLite M1 → GitHub BASE-SQL3
DATE=$(date +%Y-%m-%d)
REPO="/tmp/BASE-SQL3"
BACKUP_DIR="$REPO/backups/m1/$DATE"

# Sync repo
git -C "$REPO" pull --rebase -q 2>/dev/null
mkdir -p "$BACKUP_DIR"

# Dump toutes les DBs
for db in /home/pamerys/jarvis-master.db /home/pamerys/jarvis.db \
          $(find /home/pamerys -maxdepth 3 -name "*.db" -size +10k 2>/dev/null | grep -v restore-sdb1); do
    name=$(basename "$db" .db)
    sqlite3 "$db" ".dump" 2>/dev/null | gzip > "$BACKUP_DIR/${name}.sql.gz"
done

# Push
git -C "$REPO" add backups/
git -C "$REPO" commit -m "backup(m1): auto $(date +%Y-%m-%d)" 2>/dev/null
git -C "$REPO" push origin main -q 2>/dev/null
echo "[$(date)] backup SQL M1 OK → GitHub BASE-SQL3/$DATE"
