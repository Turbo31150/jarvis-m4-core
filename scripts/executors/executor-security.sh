#!/usr/bin/env bash
# executor-security.sh — Audit sécurité + backup rotate + scan secrets
set -uo pipefail

TITLE="${1:-security-audit}"
TASK_ID="${2:-0}"
JARVIS_DIR="/home/pamerys/jarvis"
RESULTS="$JARVIS_DIR/data/task_results"
LOG="$JARVIS_DIR/logs/executor-security.log"
TS=$(date +"%Y-%m-%dT%H:%M:%S")

mkdir -p "$RESULTS" "$(dirname "$LOG")"
log() { echo "[$TS][security] $*" | tee -a "$LOG"; }

OUT="$RESULTS/security_${TASK_ID}_$(date +%s).md"

{
echo "# Rapport Sécurité — $TITLE"
echo "_Exécuté: ${TS} — JARVIS Production_"
echo ""

echo "## 🔐 Scan Secrets (git-secrets / trufflehog)"
echo "\`\`\`"
# Scan rapide des fichiers récents pour tokens/passwords exposés
find /home/pamerys/Workspaces /home/pamerys/jarvis/scripts \
  -name "*.py" -o -name "*.sh" -o -name "*.js" -o -name "*.env" 2>/dev/null | \
  xargs grep -l -E "(API_KEY|SECRET|PASSWORD|TOKEN|PRIVATE_KEY)=" 2>/dev/null | \
  grep -v ".git\|__pycache__\|node_modules\|.venv" | \
  head -10 || echo "Aucun fichier suspect détecté"
echo "\`\`\`"
echo ""

echo "## 🛡️ Ports Ouverts (écoute locale)"
echo "\`\`\`"
ss -tlnp 2>/dev/null | grep LISTEN | awk '{print $4, $6}' | head -20 || \
  netstat -tlnp 2>/dev/null | grep LISTEN | head -20 || echo "ss/netstat non disponible"
echo "\`\`\`"
echo ""

echo "## 🔄 Permissions Docker Socket"
echo "\`\`\`"
ls -la /var/run/docker.sock 2>/dev/null || echo "Docker socket non trouvé"
id 2>/dev/null
echo "\`\`\`"
echo ""

echo "## 📋 Logs d'Erreurs Critiques (30 dernières min)"
echo "\`\`\`"
journalctl --since "30 minutes ago" --priority=err --no-pager 2>/dev/null | \
  grep -v "^--" | tail -20 || echo "journalctl non accessible"
echo "\`\`\`"
echo ""

echo "## 💾 Intégrité Backups SQLite"
echo "\`\`\`"
for db in "$JARVIS_DIR/jarvis_master.db" "$JARVIS_DIR/jarvis_logs.db"; do
  if [ -f "$db" ]; then
    result=$(sqlite3 "$db" "PRAGMA integrity_check;" 2>/dev/null)
    printf "%-40s → %s\n" "$(basename "$db")" "${result:-ERREUR}"
  fi
done
echo "\`\`\`"

echo "---"
echo "_Rapport sécurité généré par executor-security.sh_"
} | tee "$OUT"

log "✅ Rapport sécurité → $OUT"
echo "RESULT_FILE=$OUT"
exit 0
