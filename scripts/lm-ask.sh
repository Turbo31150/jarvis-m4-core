#!/bin/bash
# lm-ask.sh — dual-model sync M1+M2, 4 slots parallèles par défaut
# Usage : lm-ask.sh "question" [--reason] [--big] [--model ID] [--max N] [--seq]
# Mode : 4 appels parallèles (M1×2 + M2×2), premier non-vide gagne
# --reason  → deepseek-r1 sur M1+M2
# --big     → qwen3.5-35b sur M2
# --seq     → séquentiel M1→M2 (fallback)

set -e

MODEL_FAST="qwen/qwen3.5-9b"
MODEL_R1="deepseek/deepseek-r1-0528-qwen3-8b"
MODEL_BIG="qwen/qwen3.5-35b-a3b"
MODEL_CLOUD="gpt-oss:120b"      # routage cloud Ollama — 0 token facturé (gratuit ; kimi-k2.5=payant)
CLOUD_KEY_FILE="$HOME/.ollama/cloud_api_key"
MAX=3000
MODE="dual"   # dual | seq | single
USE_CLOUD=0   # --cloud → force le routage cloud ; sinon fallback auto si local KO
SYS="Tu es un assistant concis. Réponds directement en français, sans préambule."

MODELS_M1=("$MODEL_FAST" "$MODEL_R1")
MODELS_M2=("$MODEL_FAST" "$MODEL_R1")

while [[ "$1" == --* ]]; do
  case "$1" in
    --model)  MODELS_M1=("$2"); MODELS_M2=("$2"); shift 2 ;;
    --max)    MAX="$2"; shift 2 ;;
    --reason) MODELS_M1=("$MODEL_R1"); MODELS_M2=("$MODEL_R1"); shift ;;
    --big)    MODELS_M1=("$MODEL_FAST"); MODELS_M2=("$MODEL_BIG"); shift ;;
    --fast)   MODELS_M1=("$MODEL_FAST"); MODELS_M2=("$MODEL_FAST"); shift ;;
    --cloud)  USE_CLOUD=1; shift ;;
    --seq)    MODE="seq"; shift ;;
    *) shift ;;
  esac
done

PROMPT="$*"
[[ -t 0 ]] || PROMPT="$(cat)
$PROMPT"
[[ -z "$PROMPT" ]] && { echo "Usage: lm-ask.sh \"question\"" >&2; exit 1; }

M1="http://127.0.0.1:1234"
M2="http://192.168.1.26:1234"
M3_OLLAMA="http://192.168.1.113:11434"

call_model() {
  local host="$1" model="$2"
  local payload
  payload="$(jq -nc --arg m "$model" --arg s "$SYS" --arg p "$PROMPT" --argjson n "$MAX" \
    '{model:$m,messages:[{role:"system",content:$s},{role:"user",content:$p}],max_tokens:$n,temperature:0.2,enable_thinking:false}')"
  curl -s -m 120 "$host/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d "$payload" \
    | jq -r '(.choices[0].message.content // .choices[0].message.reasoning_content) // empty' 2>/dev/null
}

call_ollama() {
  local base="${1:-http://127.0.0.1:11434}" model="${2:-$OLLAMA_MODEL}"
  curl -s -m 60 "$base/api/generate" \
    -d "$(jq -nc --arg m "$model" --arg p "$SYS\n\n$PROMPT" '{model:$m,prompt:$p,stream:false}')" \
    | jq -r '.response // empty' 2>/dev/null
}

# Routage cloud Ollama — API hébergée ollama.com, 0 token facturé (clé Bearer)
call_cloud() {
  local key; key="${OLLAMA_API_KEY:-$(cat "$CLOUD_KEY_FILE" 2>/dev/null)}"
  [[ -z "$key" ]] && return 1
  curl -s -m 180 "https://ollama.com/api/chat" \
    -H "Authorization: Bearer $key" \
    -d "$(jq -nc --arg m "$MODEL_CLOUD" --arg s "$SYS" --arg p "$PROMPT" \
        '{model:$m,messages:[{role:"system",content:$s},{role:"user",content:$p}],stream:false}')" \
    | jq -r '.message.content // empty' 2>/dev/null
}

# Auto-détection du meilleur modèle Ollama LOCAL installé (autonomie M4 en solo)
# M4 = CPU only (pas de GPU Ollama) → on privilégie les modèles LÉGERS pour ne pas saturer.
# Les modèles lourds (7b/8b) restent accessibles via --big.
OLLAMA_MODEL="$(curl -s -m 2 http://127.0.0.1:11434/api/tags 2>/dev/null | jq -r '
  ([.models[].name]) as $m
  | (["gemma3:4b","qwen3:1.7b","llama3.2:latest","llama3.2","qwen2.5:1.5b","qwen2.5:7b","llama3.1:8b","deepseek-r1:7b"][]
     | select(. as $p | $m | index($p))) // $m[0] // empty' 2>/dev/null | head -1)"
[[ -z "$OLLAMA_MODEL" ]] && OLLAMA_MODEL="gemma3:4b"
# --big en solo M4 → bascule sur le modèle local le plus capable présent
[[ "${MODELS_M2[0]}" == "$MODEL_BIG" ]] && OLLAMA_BIG="$(curl -s -m 2 http://127.0.0.1:11434/api/tags 2>/dev/null | jq -r '
  ([.models[].name]) as $m
  | (["qwen2.5:7b","llama3.1:8b","deepseek-r1:7b","gemma3:4b"][]
     | select(. as $p | $m | index($p))) // empty' 2>/dev/null | head -1)" && [[ -n "$OLLAMA_BIG" ]] && OLLAMA_MODEL="$OLLAMA_BIG"

# Vérif connectivité (1s timeout)
M1_UP=0; M2_UP=0; OL1_UP=0; OL3_UP=0
curl -s -m 1 "$M1/v1/models" >/dev/null 2>&1 && M1_UP=1
curl -s -m 1 "$M2/v1/models" >/dev/null 2>&1 && M2_UP=1
curl -s -m 1 http://127.0.0.1:11434/api/tags >/dev/null 2>&1 && OL1_UP=1
curl -s -m 1 "$M3_OLLAMA/api/tags" >/dev/null 2>&1 && OL3_UP=1

# --cloud : routage cloud direct (prioritaire), 0 token facturé
if [[ $USE_CLOUD -eq 1 ]]; then
  R="$(call_cloud)"; [[ -n "$R" ]] && { echo "$R"; exit 0; }
  echo "✘ Cloud KO (ollama signin requis ?)" >&2
fi

# Si aucun backend local/LAN : tenter le cloud en dernier recours avant d'abandonner
if [[ $M1_UP -eq 0 && $M2_UP -eq 0 && $OL1_UP -eq 0 && $OL3_UP -eq 0 ]]; then
  R="$(call_cloud)"; [[ -n "$R" ]] && { echo "$R"; exit 0; }
  echo "✘ Aucun backend dispo (local + cloud)" >&2; exit 2
fi

if [[ "$MODE" == "dual" ]]; then
  # === MODE DUAL : M1×2 + M2×2 en parallèle — premier gagne ===
  TMPF="$(mktemp)"
  PIDS=()

  [[ $M1_UP -eq 1 ]] && for m in "${MODELS_M1[@]}"; do
    ( R="$(call_model "$M1" "$m")"; [[ -n "$R" ]] && echo "$R" > "$TMPF" ) &
    PIDS+=($!)
  done

  [[ $M2_UP -eq 1 ]] && for m in "${MODELS_M2[@]}"; do
    ( R="$(call_model "$M2" "$m")"; [[ -n "$R" ]] && echo "$R" > "$TMPF" ) &
    PIDS+=($!)
  done

  # OL1 + OL3 (M3 Ollama) si aucun LMStudio dispo
  [[ $OL1_UP -eq 1 && ${#PIDS[@]} -eq 0 ]] && {
    ( R="$(call_ollama "http://127.0.0.1:11434" "$OLLAMA_MODEL")"; [[ -n "$R" ]] && echo "$R" > "$TMPF" ) &
    PIDS+=($!)
  }
  [[ $OL3_UP -eq 1 && ${#PIDS[@]} -le 0 ]] && {
    ( R="$(call_ollama "$M3_OLLAMA" "deepseek-r1:7b")"; [[ -n "$R" ]] && echo "$R" > "$TMPF" ) &
    PIDS+=($!)
  }

  # Poll max 120s — premier résultat non-vide gagne
  for i in $(seq 1 240); do
    sleep 0.5
    if [[ -s "$TMPF" ]]; then
      cat "$TMPF"; rm -f "$TMPF"
      kill "${PIDS[@]}" 2>/dev/null
      exit 0
    fi
  done
  rm -f "$TMPF"; kill "${PIDS[@]}" 2>/dev/null
  # Fallback cloud si le local n'a rien rendu à temps
  R="$(call_cloud)"; [[ -n "$R" ]] && { echo "$R"; exit 0; }
  echo "✘ Timeout dual-mode (cloud KO aussi)" >&2; exit 2

else
  # === MODE SEQ : M1 → M2 → OL1 ===
  for m in "${MODELS_M1[@]}"; do
    [[ $M1_UP -eq 1 ]] && { R="$(call_model "$M1" "$m")"; [[ -n "$R" ]] && echo "$R" && exit 0; }
  done
  for m in "${MODELS_M2[@]}"; do
    [[ $M2_UP -eq 1 ]] && { R="$(call_model "$M2" "$m")"; [[ -n "$R" ]] && echo "$R" && exit 0; }
  done
  [[ $OL3_UP -eq 1 ]] && { R="$(call_ollama "$M3_OLLAMA" "gemma3:4b")"; [[ -n "$R" ]] && echo "$R" && exit 0; }
  [[ $OL1_UP -eq 1 ]] && { R="$(call_ollama)"; [[ -n "$R" ]] && echo "$R" && exit 0; }
  R="$(call_cloud)"; [[ -n "$R" ]] && echo "$R" && exit 0
  echo "✘ Tous backends ont échoué (cloud inclus)" >&2; exit 2
fi
