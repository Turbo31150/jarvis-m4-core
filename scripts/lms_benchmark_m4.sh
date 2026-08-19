#!/bin/bash
# ====================================================
# JARVIS — LM Studio Benchmark Massif M4
# RTX 3050 Laptop 4Go — Modèles adaptés 4Go VRAM
# ====================================================

TARGET_IP="100.124.121.16"
LMS_PORT=1234
RESULTS_FILE="$HOME/jarvis/benchmarks/lms_m4_$(date +%Y%m%d_%H%M%S).json"
mkdir -p ~/jarvis/benchmarks

echo "🚀 BENCHMARK LM Studio M4 — RTX 3050 4Go"
echo "==========================================="

MODELS_TO_TEST=(
  "qwen2.5-coder-1.5b-instruct"
  "qwen2.5-coder-3b-instruct"
  "phi-3.5-mini-instruct"
  "gemma-3-1b-instruct"
  "llama-3.2-3b-instruct"
  "deepseek-r1-distill-qwen-1.5b"
)

PROMPT_COURT="Dis bonjour en une phrase."
PROMPT_CODE="Ecris une fonction Python qui calcule la suite de Fibonacci."
PROMPT_LONG="Explique en détail le fonctionnement d'un réseau de neurones convolutif."

echo "[" > "$RESULTS_FILE"
FIRST=1

for MODEL in "${MODELS_TO_TEST[@]}"; do
  echo ""
  echo "📊 Test : $MODEL"
  
  # Charger le modèle via LM Studio API
  START=$(date +%s%N)
  
  RESPONSE=$(curl -s -X POST "http://${TARGET_IP}:${LMS_PORT}/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d "{
      \"model\": \"$MODEL\",
      \"messages\": [{\"role\": \"user\", \"content\": \"$PROMPT_COURT\"}],
      \"max_tokens\": 100,
      \"temperature\": 0.1
    }" 2>&1)
  
  END=$(date +%s%N)
  ELAPSED_MS=$(( (END - START) / 1000000 ))
  
  TOKENS=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('usage',{}).get('completion_tokens',0))" 2>/dev/null || echo "0")
  TPS=$(echo "$TOKENS $ELAPSED_MS" | awk '{if($2>0) printf "%.1f", $1*1000/$2; else print "0"}')
  
  echo "  ⏱️  Latence : ${ELAPSED_MS}ms | Tokens: $TOKENS | TPS: $TPS tok/s"
  
  [ $FIRST -eq 0 ] && echo "," >> "$RESULTS_FILE"
  FIRST=0
  cat >> "$RESULTS_FILE" << JSON
  {
    "model": "$MODEL",
    "latency_ms": $ELAPSED_MS,
    "tokens": $TOKENS,
    "tokens_per_sec": $TPS,
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  }
JSON
done

echo "]" >> "$RESULTS_FILE"
echo ""
echo "✅ Benchmark terminé → $RESULTS_FILE"
echo ""
echo "📊 CLASSEMENT PAR TPS :"
python3 - "$RESULTS_FILE" << 'PY'
import json, sys
with open(sys.argv[1]) as f:
    data = json.load(f)
sorted_data = sorted(data, key=lambda x: float(x.get('tokens_per_sec', 0)), reverse=True)
for i, m in enumerate(sorted_data):
    print(f"  #{i+1} {m['model'][:40]:<40} → {m['tokens_per_sec']} tok/s ({m['latency_ms']}ms)")
PY
