#!/usr/bin/env bash
# JARVIS Cluster Warmer — Production
# M2 porteur (deepseek-r1 + 9b) | M3 secondaire | OL1 rapide
# M1 llama-server RPC: activé manuellement si LM Studio M1 arrêté
set -uo pipefail

M2="http://192.168.1.26:1234"
M3="http://192.168.1.113:1234"
OL1="http://127.0.0.1:11434"
M1_LLAMA="http://127.0.0.1:8080"
LOG="/tmp/cluster-warmer.log"

warm_lmstudio() {
    local host="$1" model="$2" label="$3"
    local state
    state=$(curl -s --max-time 3 "$host/api/v0/models" 2>/dev/null | \
        python3 -c "import json,sys; d=json.load(sys.stdin); \
        m=next((x for x in d.get('data',[]) if x['id']=='$model'), None); \
        print(m['state'] if m else 'absent')" 2>/dev/null || echo "KO")
    if [ "$state" = "loaded" ]; then
        echo "✅ $label/$model"
    elif [ "$state" = "loading" ]; then
        echo "⏳ $label/$model loading..."
    elif [ "$state" = "not-loaded" ]; then
        echo "🔁 $label/$model triggering load..."
        curl -s --max-time 5 "$host/v1/chat/completions" \
            -H "Content-Type: application/json" \
            -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_tokens\":1}" \
            > /dev/null 2>&1 &
    else
        echo "⚠  $label/$model → $state"
    fi
}

echo "[$(date '+%H:%M:%S')] JARVIS Cluster Warmer START" | tee -a "$LOG"

# M2 — porteur principal (modèles lourds)
warm_lmstudio "$M2" "deepseek/deepseek-r1-0528-qwen3-8b" "M2"
warm_lmstudio "$M2" "qwen/qwen3.5-9b" "M2"

# M3 — secondaire
if curl -s --max-time 2 "$M3/api/v0/models" > /dev/null 2>&1; then
    warm_lmstudio "$M3" "deepseek/deepseek-r1-0528-qwen3-8b" "M3"
    warm_lmstudio "$M3" "qwen/qwen3.5-9b" "M3"
    echo "✅ M3 en ligne"
else
    echo "⚠  M3 hors ligne"
fi

# OL1 — ultra-rapide
if curl -s --max-time 2 "$OL1/api/tags" > /dev/null 2>&1; then
    echo "✅ OL1 qwen3:1.7b + kimi-cloud disponibles"
else
    echo "⚠  OL1 hors ligne"
fi

# M1 llama-server RPC (optionnel — actif si LM Studio M1 arrêté)
if curl -s --max-time 2 "$M1_LLAMA/v1/models" > /dev/null 2>&1; then
    echo "✅ M1 llama-server :8080 (GPU pool M1+M3) ACTIF"
else
    echo "ℹ  M1 llama-server :8080 inactif (mode LM Studio)"
fi

echo "[$(date '+%H:%M:%S')] Cluster warmer DONE" | tee -a "$LOG"
