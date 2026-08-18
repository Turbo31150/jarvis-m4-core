#!/usr/bin/env bash
# executor-cluster.sh — Warmup et bench cluster LLM en production réelle
# Noeuds: M1=192.168.0.10:1234 M2=127.0.0.1:18800 M4=192.168.0.10:11235 OL1=127.0.0.1:11434
set -uo pipefail

TITLE="${1:-cluster-warmup}"
TASK_ID="${2:-0}"
JARVIS_DIR="/home/pamerys/jarvis"
DB="$JARVIS_DIR/jarvis_master.db"
RESULTS="$JARVIS_DIR/data/task_results"
LOG="$JARVIS_DIR/logs/executor-cluster.log"
TS=$(date +"%Y-%m-%dT%H:%M:%S")
LM="$JARVIS_DIR/scripts/lm-ask.sh"

mkdir -p "$RESULTS" "$(dirname "$LOG")"
log() { echo "[$TS][cluster] $*" | tee -a "$LOG"; }

OUT="$RESULTS/cluster_${TASK_ID}_$(date +%s).md"

# ─── Ping rapide d'un endpoint LLM ───
ping_llm() {
  local host=$1 port=$2 name=$3
  local start=$SECONDS
  local res
  res=$(curl -sf --max-time 5 "http://$host:$port/v1/models" 2>/dev/null | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin)
  models=[m['id'] for m in d.get('data',[])]
  print('UP | models: ' + ', '.join(models[:3]))
except:
  print('UP (format inconnu)')
" 2>/dev/null) || res="DOWN (timeout)"
  local elapsed=$((SECONDS-start))
  echo "| $name | $res | ${elapsed}s |"
}

ping_ollama() {
  local res
  res=$(curl -sf --max-time 5 "http://127.0.0.1:11434/api/tags" 2>/dev/null | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin)
  models=[m['name'] for m in d.get('models',[])]
  print('UP | ' + ', '.join(models[:4]))
except:
  print('UP')
" 2>/dev/null) || res="DOWN"
  echo "| OL1 (127.0.0.1:11434) | $res | - |"
}

{
echo "# Rapport Cluster LLM — $TITLE"
echo "_Exécuté: ${TS}_"
echo ""

echo "## 🌐 État des Noeuds"
echo "| Noeud | Status | Latence |"
echo "|---|---|---|"
ping_llm 192.168.0.10 1234 "M1 (192.168.0.10)"
ping_llm 127.0.0.1 1234 "M2 (127.0.0.1)"
ping_llm 192.168.0.10 11235 "M4 (192.168.0.10:11235 — qwen3.5-9b)"
ping_ollama
echo ""

echo "## ⚡ Test Inférence Rapide (lm-ask)"
if [ -f "$LM" ]; then
  echo "\`\`\`"
  t0=$SECONDS
  result=$(bash "$LM" "Réponds juste: pong" 2>/dev/null | head -2 || echo "timeout/erreur")
  elapsed=$((SECONDS-t0))
  echo "Prompt: 'Réponds juste: pong'"
  echo "Réponse: $result"
  echo "Temps: ${elapsed}s"
  echo "\`\`\`"
else
  echo "⚠️ lm-ask.sh non trouvé"
fi
echo ""

echo "## 📊 Recommandation Routage"
echo "- Tâches urgentes → M1 (qwen3.5-9b, latence < 5s)"
echo "- Raisonnement → M2 (deepseek-r1, latence ~10s)"
echo "- Petites tâches → OL1 (gemma3:4b, latence < 3s)"
echo ""

echo "---"
echo "_Rapport cluster généré par executor-cluster.sh_"
} | tee "$OUT"

log "✅ Rapport cluster → $OUT"
echo "RESULT_FILE=$OUT"
exit 0
