#!/usr/bin/env bash
# ============================================================
# M1 PRODUCTION — llama-server ik_llama.cpp
# Remplace LM Studio local sur M1 quand activé
# Poole GPU M1 (40GB) + RPC M3 (si disponible)
# ============================================================
set -uo pipefail

LLAMA_SERVER="/opt/ik_llama.cpp/build/bin/llama-server"
MODEL_9B="$HOME/.lmstudio/models/lmstudio-community/Qwen3.5-9B-GGUF/Qwen3.5-9B-Q4_K_M.gguf"
MODEL_DEEPSEEK="$HOME/.lmstudio/models/lmstudio-community/DeepSeek-R1-0528-Qwen3-8B-GGUF/DeepSeek-R1-0528-Qwen3-8B-Q4_K_M.gguf"
PORT="${1:-8080}"
M3_IP="192.168.1.113"
M3_RPC_PORT="50052"

# Choisir le modèle
MODEL="${MODEL_9B}"
if [ "${2:-}" = "deepseek" ]; then
  MODEL="${MODEL_DEEPSEEK}"
fi

# Tester si M3 rpc-server est disponible
RPC_ARGS=""
if timeout 2 bash -c "echo >/dev/tcp/${M3_IP}/${M3_RPC_PORT}" 2>/dev/null; then
  RPC_ARGS="--rpc ${M3_IP}:${M3_RPC_PORT}"
  echo "✅ M3 rpc-server détecté → GPU pooling activé"
else
  echo "⚠  M3 non disponible → GPU M1 seuls (40GB)"
fi

echo "Modèle: $MODEL"
echo "Port: $PORT"
echo "RPC: ${RPC_ARGS:-none}"

# Utiliser GPU1+2+4 (éviter GPU0=display et GPU3=presque plein)
# Si LM Studio est arrêté sur M1, utiliser TOUS les GPU
CUDA_VISIBLE_DEVICES=0,1,2,4

# Tuer instance précédente
pkill -f "llama-server.*${PORT}" 2>/dev/null || true
sleep 1

CUDA_VISIBLE_DEVICES=0,1,2,4 nohup "$LLAMA_SERVER" \
  --model "$MODEL" \
  --port "$PORT" \
  --host "0.0.0.0" \
  --n-gpu-layers 99 \
  ${RPC_ARGS} \
  --ctx-size 16384 \
  --parallel 4 \
  --threads 8 \
  > /tmp/llama-server-${PORT}.log 2>&1 &

PID=$!
echo "PID: $PID"
sleep 8

if ss -tlnp | grep -q ":${PORT}"; then
  echo "✅ llama-server :${PORT} ACTIF"
  curl -s --max-time 3 "http://127.0.0.1:${PORT}/v1/models" 2>/dev/null | \
    python3 -c "import json,sys; d=json.load(sys.stdin); print('modèles:', [m['id'] for m in d.get('data',[])])" 2>/dev/null
else
  echo "❌ ÉCHEC — voir /tmp/llama-server-${PORT}.log"
  tail -20 /tmp/llama-server-${PORT}.log
fi
