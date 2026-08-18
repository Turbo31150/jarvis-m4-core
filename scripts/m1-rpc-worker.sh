#!/bin/bash
# M1 — RPC Worker pour M2 coordinateur
# Expose les 3 GPUs de M1 via llama.cpp RPC
# M2 se connecte sur 192.168.1.85:50052

set -e

RPC_PORT=50052
LLAMA_BIN="$HOME/llama.cpp/build/bin/rpc-server"

if ! [ -x "$LLAMA_BIN" ]; then
    echo "[ERROR] rpc-server not found at $LLAMA_BIN"
    exit 1
fi

# Vérif CUDA dispo
nvidia-smi -L 2>/dev/null || { echo "[ERROR] NVIDIA GPUs not available"; exit 1; }

echo "[M1-RPC] Starting RPC worker on 0.0.0.0:$RPC_PORT"
echo "[M1-RPC] GPUs exposed to M2 coordinator"

exec "$LLAMA_BIN" \
    --host 0.0.0.0 \
    --port "$RPC_PORT"
