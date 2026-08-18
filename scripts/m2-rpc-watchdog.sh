#!/bin/bash
# M2 RPC Watchdog — llama-server RPC M1, CUDA local désactivé
M1_RPC="192.168.1.85:50052"
LLAMA_BIN="$HOME/llama.cpp/build/bin/llama-server"
MODELS_DIR="$HOME/.lmstudio/models/lmstudio-community"
CHECK_INTERVAL=30
LOG="/tmp/m2-rpc-watchdog.log"

# Format: "gguf|alias|parallel|ctx|gpu_device|batch"
declare -A SERVERS=(
    [8080]="Qwen3.5-9B-GGUF/Qwen3.5-9B-Q4_K_M.gguf|qwen3.5-9b|2|4096|2|512"
    [8082]="DeepSeek-R1-0528-Qwen3-8B-GGUF/DeepSeek-R1-0528-Qwen3-8B-Q4_K_M.gguf|deepseek-r1|1|4096|1|256"
)

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }

rpc_alive() { timeout 2 bash -c "echo >/dev/tcp/192.168.1.85/50052" 2>/dev/null; }

start_server() {
    local port=$1; local cfg="${SERVERS[$port]}"
    local model=$(echo $cfg | cut -d'|' -f1)
    local alias=$(echo $cfg | cut -d'|' -f2)
    local parallel=$(echo $cfg | cut -d'|' -f3)
    local ctx=$(echo $cfg | cut -d'|' -f4)
    local gpu_dev=$(echo $cfg | cut -d'|' -f5)
    local batch=$(echo $cfg | cut -d'|' -f6)
    local model_path="$MODELS_DIR/$model"
    local rpc_arg=""
    # DeepSeek (8082) : no RPC — causes hang with this llama.cpp build
    if [[ "$port" == "8080" ]]; then
        rpc_alive && rpc_arg="--rpc $M1_RPC" && log "[LAUNCH:$port] $alias GPU$gpu_dev + RPC M1" \
                   || log "[LAUNCH:$port] $alias GPU$gpu_dev LOCAL (M1 down)"
    else
        log "[LAUNCH:$port] $alias GPU$gpu_dev LOCAL (no-RPC)"
    fi
    CUDA_VISIBLE_DEVICES="$gpu_dev" "$LLAMA_BIN" \
        --model "$model_path" --host 0.0.0.0 --port "$port" \
        -ngl 999 --ctx-size "$ctx" --parallel "$parallel" \
        --batch-size "$batch" --ubatch-size "$batch" \
        --timeout 300 --threads 4 --no-warmup \
        -fa on --cache-ram 0 \
        --alias "$alias" $rpc_arg &>"/tmp/llama-${port}.log" &
    sleep 8
    STATUS=$(curl -s "http://localhost:$port/health" 2>/dev/null)
    echo "$STATUS" | grep -q "ok\|unavailable" && log "[OK:$port] $STATUS" || log "[WARN:$port] no response"
}

log "[WATCHDOG] Start — ports 8080 8082"
while true; do
    for port in 8080 8082; do
        if ! pgrep -f "llama-server.*port $port" >/dev/null 2>&1; then
            log "[DEAD:$port] relance"
            start_server $port
        fi
    done
    sleep "$CHECK_INTERVAL"
done
