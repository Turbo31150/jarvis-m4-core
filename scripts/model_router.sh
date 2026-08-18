#!/bin/bash
# JARVIS Model Router — bascule automatique Ollama/Antigravity/LM Studio
# Usage: model_router.sh <task_type> <prompt> [machine]

TASK="${1:-general}"
PROMPT="${2:-test}"
MACHINE="${3:-M1}"
LOG_DB="/home/pamerys/jarvis/cowork_engine.db"
# Parc réel 2026-08-14 : M4 (ici) + M6 (câble direct) + Rémi (Tailscale).
# LM Studio M6 = backend par défaut ; hub :18800 et Ollama local en repli.
LM_M6="${LM_M6:-http://10.42.0.230:1234}"
OL1="http://127.0.0.1:11434"
REMI="${REMI:-http://100.113.121.61:11434}"
HUB="http://127.0.0.1:18800"
TS=$(date -u +%Y-%m-%dT%H:%M:%S)

# Routing table: task_type → modèle préféré
case "$TASK" in
  "reasoning"|"debug")  MODEL="deepseek-r1:7b";  BACKEND="ollama" ;;
  "fast"|"micro")       MODEL="qwen2.5:1.5b";    BACKEND="ollama" ;;
  "general"|"code")     MODEL="qwen3:1.7b";       BACKEND="ollama" ;;
  "heavy"|"cloud")      MODEL="gpt-oss:20b-cloud";  BACKEND="antigravity" ;;
  *)                    MODEL="gemma3:4b";         BACKEND="ollama" ;;
esac

# Test disponibilité Ollama
OL1_STATUS=$(curl -s --max-time 2 "$OL1/api/tags" 2>/dev/null | python3 -c "import json,sys; print('up')" 2>/dev/null || echo "down")

# Bascule si Ollama DOWN → gpt-oss:20b-cloud (Antigravity)
if [ "$OL1_STATUS" = "down" ] && [ "$BACKEND" = "ollama" ]; then
  MODEL="gpt-oss:20b-cloud"
  BACKEND="antigravity_fallback"
fi

# LM Studio check M1
LM1_STATUS=$(curl -s --max-time 1 "$LM_M6/v1/models" 2>/dev/null | python3 -c "import json,sys; print('up')" 2>/dev/null || echo "down")
if [ "$LM1_STATUS" = "up" ] && [ "$TASK" = "code" ]; then
  BACKEND="lmstudio_m1"
fi

START_MS=$(date +%s%3N)

# Appel selon backend
if [ "$BACKEND" = "ollama" ] || [ "$BACKEND" = "antigravity_fallback" ]; then
  BODY=$(jq -nc --arg m "$MODEL" --arg p "$PROMPT" '{model:$m,prompt:$p,stream:false}')
  REPLY=$(curl -s --max-time 30 "$OL1/api/generate" \
    -d "$BODY" 2>/dev/null \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('response','')[:200])" 2>/dev/null)
fi

END_MS=$(date +%s%3N)
LATENCY=$((END_MS - START_MS))

# Enregistrement usage
python3 - "$LOG_DB" "$TS" "$MACHINE" "$MODEL" "$BACKEND" "$TASK" "$LATENCY" <<'PY' 2>/dev/null
import sqlite3, sys
log_db, ts, machine, model, backend, task, latency = sys.argv[1:8]
conn = sqlite3.connect(log_db)
conn.execute('''INSERT INTO model_usage_log (ts, machine, model, backend, task_type, latency_ms, source, routed_via)
  VALUES (?,?,?,?,?,?,?,?)''',
  (ts, machine, model, backend, task, int(latency), 'model_router', backend))
conn.commit()
conn.close()
print(f'[router] {machine}/{model} via {backend} | {latency}ms')
PY

echo "$REPLY"
