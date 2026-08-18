#!/bin/bash
# Script automation e-commerce — À lancer via cron ou jarvis-autopilot

set -e

LOGFILE="/tmp/ecommerce-automation.log"
echo "[$(date)] Automation e-commerce" >> $LOGFILE

# 1. Vérifier que les boutiques sont live
for site in alkymia-os jarvis-delmas admin-ia agent-sans-coder prof-ia transcription-ia; do
    status=$(curl -s -o /dev/null -w "%{http_code}" "https://${site}.netlify.app/checkout")
    [ "$status" = "200" ] && echo "✅ $site" >> $LOGFILE || echo "⚠️  $site ($status)" >> $LOGFILE
done

# 2. Déployer les changements si des fichiers ont changé
for repo in /home/pamerys/alkymia-site /home/pamerys/jarvis-delmas-site /home/pamerys/Documents/micro-sites/*/; do
    if [ -d "$repo" ]; then
        cd "$repo"
        if git status --short | grep -q checkout; then
            git add checkout/
            git commit -m "chore: sync ecommerce" 2>/dev/null || true
            git push 2>/dev/null || true
        fi
    fi
done

echo "[$(date)] ✅ Automation terminée" >> $LOGFILE
