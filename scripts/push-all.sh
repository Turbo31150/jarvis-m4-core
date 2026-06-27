#!/bin/bash
set -e

echo "🚀 JARVIS Push-All — $(date +%H:%M:%S)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Vérifier et démarrer services
echo ""
echo "📌 Services systemctl…"
for SVC in jarvis-voice-widget jarvis-thermal-agent jarvis-multiagent; do
    if systemctl --user is-active --quiet "$SVC.service" 2>/dev/null; then
        echo "✅ $SVC — actif"
    else
        echo "⚠️  $SVC — inactif → restart"
        systemctl --user start "$SVC.service" 2>/dev/null || echo "   (non-fatal)"
    fi
done

# 2. Backup SQL rapide
echo ""
echo "📌 Backup SQL…"
mkdir -p ~/BASE-SQL3/m4/sql-"$(date +%Y%m%d)"

for DB in ~/jarvis/budget/budget.db ~/jarvis/planning.db ~/jarvis/notes.db; do
    if [ -f "$DB" ]; then
        BACKUP_DIR=~/BASE-SQL3/m4/sql-"$(date +%Y%m%d)"
        BASENAME=$(basename "$DB" .db)
        if sqlite3 "$DB" .dump 2>/dev/null | gzip > "$BACKUP_DIR/${BASENAME}-latest.sql.gz"; then
            echo "✅ $BASENAME sauvegardé"
        else
            echo "⚠️  $BASENAME — erreur backup (non-fatal)"
        fi
    fi
done

# 3. Push BASE-SQL3
echo ""
echo "📌 Push BASE-SQL3…"
if [ -d ~/BASE-SQL3/.git ]; then
    cd ~/BASE-SQL3 || exit 1
    git add -A 2>/dev/null || true
    if ! git diff --cached --quiet 2>/dev/null; then
        if git commit -m "auto-push $(date +%Y-%m-%d_%H:%M)" 2>&1 | tail -1; then
            if git push 2>&1 | tail -1; then
                echo "✅ BASE-SQL3 pushé"
            else
                echo "⚠️  Push BASE-SQL3 échoué (non-fatal)"
            fi
        fi
    else
        echo "ℹ️  BASE-SQL3 — rien à pousser"
    fi
else
    echo "⚠️  BASE-SQL3 — pas un repo git"
fi

# 4. Push machine-m4-pamerys
echo ""
echo "📌 Push machine-m4-pamerys…"
if [ -d ~/machine-m4-pamerys/.git ]; then
    cd ~/machine-m4-pamerys || exit 1
    git add -A 2>/dev/null || true
    if ! git diff --cached --quiet 2>/dev/null; then
        if git commit -m "auto-push $(date +%Y-%m-%d_%H:%M)" 2>&1 | tail -1; then
            if git push 2>&1 | tail -1; then
                echo "✅ machine-m4-pamerys pushé"
            else
                echo "⚠️  Push machine-m4-pamerys échoué (non-fatal)"
            fi
        fi
    else
        echo "ℹ️  machine-m4-pamerys — rien à pousser"
    fi
else
    echo "⚠️  machine-m4-pamerys — pas un repo git"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Push-All terminé — $(date +%H:%M:%S)"
