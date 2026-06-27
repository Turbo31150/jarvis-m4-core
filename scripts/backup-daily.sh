#!/bin/bash
# Sauvegarde quotidienne JARVIS PAMERYS M4
# Cron: 0 22 * * * bash /home/pamerys/jarvis/scripts/backup-daily.sh
# Alias: backup-now

BACKUP_DIR="$HOME/Backups"
mkdir -p "$BACKUP_DIR"
DATE=$(date +%Y-%m-%d)

echo "📦 Sauvegarde JARVIS $DATE..."

# 1. Documents (max 500MB)
if [ -d "$HOME/Documents" ]; then
    tar czf "$BACKUP_DIR/docs-$DATE.tar.gz" "$HOME/Documents/" 2>/dev/null
    DOC_SIZE=$(du -sh "$BACKUP_DIR/docs-$DATE.tar.gz" 2>/dev/null | cut -f1)
    echo "✅ Documents: $DOC_SIZE"
fi

# 2. SQLite databases
for DB in "$HOME/jarvis/budget/budget.db" "$HOME/jarvis/planning.db" "$HOME/.openclaw/metrics.db"; do
    if [ -f "$DB" ]; then
        BASENAME=$(basename "$DB" .db)
        sqlite3 "$DB" .dump 2>/dev/null | gzip > "$BACKUP_DIR/${BASENAME}-$DATE.sql.gz"
        echo "✅ DB: $BASENAME"
    fi
done

# 3. Rotation: garder 7 jours max
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete 2>/dev/null
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete 2>/dev/null

# 4. Notification système
if command -v notify-send &> /dev/null; then
    notify-send "JARVIS Backup" "✅ Sauvegarde $DATE terminée" 2>/dev/null
fi

echo "✅ Backup $DATE complet — $BACKUP_DIR"
