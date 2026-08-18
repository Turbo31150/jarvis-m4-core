#!/bin/bash
# M2 — Coordinateur modèles, distribue sur M1/M3 via RPC
# Usage: ./m2-model-server.sh [model_name] [port]
#   model_name: deepseek-r1 | qwen3.5-9b | qwen2.5-coder-14b (défaut: qwen3.5-9b)

MODEL_NAME="${1:-qwen3.5-9b}"
PORT="${2:-8080}"
LLAMA_BIN="$HOME/llama.cpp/build/bin/llama-server"
MODELS_DIR="$HOME/.lmstudio/models/lmstudio-community"
M1_RPC="192.168.1.85:50052"
M3_RPC="192.168.1.133:50052"

# ── Profils par modèle ─────────────────────────────────────────────────────
# Format: "gguf_path|ctx_size|parallel|gpu_device|batch_size"
declare -A MODELS
MODELS[qwen3.5-9b]="Qwen3.5-9B-GGUF/Qwen3.5-9B-Q4_K_M.gguf|8192|4|1|512"
MODELS[deepseek-r1]="DeepSeek-R1-0528-Qwen3-8B-GGUF/DeepSeek-R1-0528-Qwen3-8B-Q4_K_M.gguf|8192|2|2|256"
MODELS[qwen2.5-coder-14b]="Qwen2.5-Coder-14B-Instruct-GGUF/Qwen2.5-Coder-14B-Instruct-Q4_K_M.gguf|4096|2|1|256"

CFG="${MODELS[$MODEL_NAME]}"
if [ -z "$CFG" ]; then
    echo "[ERROR] Modèle inconnu: $MODEL_NAME. Disponibles: ${!MODELS[@]}"
    exit 1
fi

IFS='|' read -r GGUF CTX PARALLEL GPU_DEV BATCH <<< "$CFG"
MODEL_PATH="$MODELS_DIR/$GGUF"

# Fallback recherche fichier
if [ ! -f "$MODEL_PATH" ]; then
    MODEL_PATH=$(find "$MODELS_DIR" -name "*.gguf" | grep -i "${MODEL_NAME//-/}" | head -1)
fi
if [ -z "$MODEL_PATH" ] || [ ! -f "$MODEL_PATH" ]; then
    echo "[ERROR] GGUF introuvable: $GGUF"
    find "$MODELS_DIR" -name "*.gguf" | sed 's|.*/||'
    exit 1
fi

# ── Détection RPC ─────────────────────────────────────────────────────────
RPC_ARGS=""
for rpc in "$M1_RPC" "$M3_RPC"; do
    host="${rpc%%:*}"; port_r="${rpc##*:}"
    if timeout 1 bash -c "echo >/dev/tcp/$host/$port_r" 2>/dev/null; then
        echo "[M2] RPC worker: $rpc"
        RPC_ARGS="$RPC_ARGS --rpc $rpc"
    fi
done

echo "[M2] model=$MODEL_NAME port=$PORT ctx=$CTX parallel=$PARALLEL gpu=$GPU_DEV batch=$BATCH"
echo "[M2] RPC: ${RPC_ARGS:-none (local only)}"

exec env CUDA_VISIBLE_DEVICES="$GPU_DEV" \
    "$LLAMA_BIN" \
    --model "$MODEL_PATH" \
    --host 0.0.0.0 \
    --port "$PORT" \
    -ngl 999 \
    --ctx-size "$CTX" \
    --parallel "$PARALLEL" \
    --batch-size "$BATCH" \
    --ubatch-size "$BATCH" \
    --timeout 300 \
    --threads 4 \
    --no-warmup \
    --alias "$MODEL_NAME" \
    $RPC_ARGS
