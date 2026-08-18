#!/usr/bin/env bash
# executor-infra.sh — Exécuteur INFRA en production réelle
# Tâches: boot-sequence, health-monitor, auto-healer, gpu-thermal, gpu-memory
# Usage: executor-infra.sh "<titre_tache>" [task_id]
# Output: rapport Markdown sur stdout + exit 0 (ok) / 1 (erreur)
set -uo pipefail

TITLE="${1:-infra-check}"
TASK_ID="${2:-0}"
JARVIS_DIR="/home/pamerys/jarvis"
DB="$JARVIS_DIR/jarvis_master.db"
LOG="$JARVIS_DIR/logs/executor-infra.log"
RESULTS="$JARVIS_DIR/data/task_results"
TS=$(date +"%Y-%m-%dT%H:%M:%S")

mkdir -p "$RESULTS" "$(dirname "$LOG")"

log() { echo "[$TS][infra] $*" | tee -a "$LOG"; }

# ─── Rapport MD ───────────────────────────────────────────────
OUT="$RESULTS/infra_${TASK_ID}_$(date +%s).md"
{
echo "# Rapport Infra — $TITLE"
echo "_Exécuté: ${TS} — JARVIS Production_"
echo ""

# ── Système général ──
echo "## 🖥️ Système"
echo "\`\`\`"
uptime
uname -r
echo "\`\`\`"
echo ""

# ── CPU / RAM ──
echo "## 💾 CPU & RAM"
echo "\`\`\`"
grep -E "MemTotal|MemFree|MemAvailable" /proc/meminfo
echo ""
grep "cpu MHz" /proc/cpuinfo | head -4
echo "\`\`\`"
echo ""

# ── Disques ──
echo "## 💿 Disques"
echo "\`\`\`"
df -h --output=source,size,used,avail,pcent,target | head -12
echo "\`\`\`"
echo ""

# ── GPU ──
echo "## 🎮 GPU"
echo "\`\`\`"
if command -v nvidia-smi &>/dev/null; then
  nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total \
    --format=csv,noheader 2>/dev/null || echo "nvidia-smi erreur"
else
  echo "Pas de nvidia-smi — vérifier: rocm-smi ou GPU non disponible"
  # AMD GPU fallback
  if command -v rocm-smi &>/dev/null; then
    rocm-smi --showtemp --showmeminfo vram 2>/dev/null | head -20
  fi
fi
echo "\`\`\`"
echo ""

# ── Services systemd critiques ──
echo "## ⚙️ Services Critiques"
echo "\`\`\`"
SERVICES=(
  jarvis-master.service
  jarvis-pipeline.service
  jarvis-monitor.service
  jarvis-ai-proxy.service
  health-patrol.service
  jarvis-pulse.service
  jarvis-prod-runner.service
)
for svc in "${SERVICES[@]}"; do
  status=$(systemctl is-active "$svc" 2>/dev/null || echo "unknown")
  printf "%-45s %s\n" "$svc" "$status"
done
echo "\`\`\`"
echo ""

# ── Docker ──
echo "## 🐳 Docker"
echo "\`\`\`"
docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null | head -20 || echo "Docker non accessible"
echo "\`\`\`"
echo ""

# ── Auto-heal: relance services DOWN ──
echo "## 🔧 Auto-Heal"
FIXED=0
for svc in jarvis-master.service jarvis-pipeline.service health-patrol.service; do
  if [ "$(systemctl is-active "$svc" 2>/dev/null)" != "active" ]; then
    echo "- ⚠️ $svc DOWN → relance..."
    systemctl restart "$svc" 2>/dev/null && echo "  ✅ Relancé" || echo "  ❌ Échec relance"
    FIXED=$((FIXED+1))
  else
    echo "- ✅ $svc OK"
  fi
done
[ $FIXED -eq 0 ] && echo "Tous les services critiques sont UP."
echo ""

echo "---"
echo "_Rapport généré par executor-infra.sh — JARVIS Production_"
} | tee "$OUT"

log "✅ Rapport infra produit → $OUT"
echo ""
echo "RESULT_FILE=$OUT"
exit 0
