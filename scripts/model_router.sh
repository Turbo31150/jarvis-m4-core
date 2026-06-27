#!/bin/bash
# JARVIS Model Router — bascule automatique Ollama/Antigravity/LM Studio
# Usage: model_router.sh <task_type> <prompt> [machine]

TASK="${1:-general}"
PROMPT="${2:-test}"
MACHINE="${3:-M1}"
LOG_DB="/home/pamerys/jarvis/cowork_engine.db"
OL1="http://127.0.0.1:11434"
M1_LM="http://127.0.0.1:1234"
M2_LM="http://192.168.1.26:1234"
TS=$(date -u +%Y-%m-%dT%H:%M:%S)

# Routing table: task_type → modèle préféré
case "$TASK" in
  "reasoning"|"debug")  MODEL="deepseek-r1:7b";  BACKEND="ollama" ;;
  "fast"|"micro")       MODEL="qwen2.5:1.5b";    BACKEND="ollama" ;;
  "general"|"code")     MODEL="qwen3:1.7b";       BACKEND="ollama" ;;
  "heavy"|"cloud")      MODEL="kimi-k2.5:cloud";  BACKEND="antigravity" ;;
  *)                    MODEL="gemma3:4b";         BACKEND="ollama" ;;
esac

# Test disponibilité Ollama
OL1_STATUS=$(curl -s --max-time 2 "$OL1/api/tags" 2>/dev/null | python3 -c "import json,sys; print('up')" 2>/dev/null || echo "down")

# Bascule si Ollama DOWN → kimi-k2.5:cloud (Antigravity)
if [ "$OL1_STATUS" = "down" ] && [ "$BACKEND" = "ollama" ]; then
  MODEL="kimi-k2.5:cloud"
  BACKEND="antigravity_fallback"
fi

# LM Studio check M1
LM1_STATUS=$(curl -s --max-time 1 "$M1_LM/v1/models" 2>/dev/null | python3 -c "import json,sys; print('up')" 2>/dev/null || echo "down")
if [ "$LM1_STATUS" = "up" ] && [ "$TASK" = "code" ]; then
  BACKEND="lmstudio_m1"
fi

START_MS=$(date +%s%3N)

# Appel selon backend
if [ "$BACKEND" = "ollama" ] || [ "$BACKEND" = "antigravity_fallback" ]; then
  REPLY=$(curl -s --max-time 30 "$OL1/api/generate" \
    -d "{\"model\":\"$MODEL\",\"prompt\":\"$PROMPT\",\"stream\":false}" 2>/dev/null \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('response','')[:200])" 2>/dev/null)
fi

END_MS=$(date +%s%3N)
LATENCY=$((END_MS - START_MS))

# Enregistrement usage
python3 -c "
import sqlite3, datetime
conn = sqlite3.connect('$LOG_DB')
conn.execute('''INSERT INTO model_usage_log (ts, machine, model, backend, task_type, latency_ms, source, routed_via)
  VALUES (?,?,?,?,?,?,?,?)''',
  ('$TS', '$MACHINE', '$MODEL', '$BACKEND', '$TASK', $LATENCY, 'model_router', '$BACKEND'))
conn.commit()
conn.close()
print(f'[router] {\"$MACHINE\"}/{\"$MODEL\"} via {\"$BACKEND\"} | {$LATENCY}ms')
" 2>/dev/null

echo "$REPLY"
