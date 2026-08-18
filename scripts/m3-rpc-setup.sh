#!/usr/bin/env bash
# ============================================================
# SCRIPT À EXÉCUTER SUR M3 (192.168.1.113)
# Expose les GPU de M3 comme workers RPC pour M1
# ============================================================
# 1. Cloner ik_llama.cpp (ou llama.cpp standard)
# git clone https://github.com/ggerganov/llama.cpp /opt/llama.cpp
# cd /opt/llama.cpp && mkdir build && cd build
# cmake .. -DGGML_CUDA=ON -DGGML_RPC=ON -DCMAKE_BUILD_TYPE=Release
# cmake --build . --config Release -j$(nproc)
# OU si déjà compilé, utiliser le binaire existant

# 2. Lancer rpc-server (expose TOUS les GPU de M3)
RPC_BIN="${1:-/opt/llama.cpp/build/bin/rpc-server}"
HOST="0.0.0.0"
PORT="50052"

echo "[M3 RPC] Démarrage rpc-server sur $HOST:$PORT"
echo "[M3 RPC] Exposer tous les GPU CUDA disponibles"

nohup "$RPC_BIN" \
  --host "$HOST" \
  --port "$PORT" \
  >> /tmp/rpc-server-m3.log 2>&1 &

echo "PID: $!"
sleep 2
ss -tlnp 2>/dev/null | grep "$PORT" && echo "✅ rpc-server M3 UP" || echo "❌ KO"

# 3. Firewall: autoriser M1 à accéder
echo "[M3 RPC] Si Windows: ouvrir port TCP 50052 dans le pare-feu Windows"
echo "  → Panneau de configuration → Pare-feu Windows → Règle entrante → TCP 50052"
