#!/usr/bin/env bash
# qwen-nothink.sh — Helper d'inférence LLM rapide 0-token (Qwen <think> pré-fermé)
# Évite les réponses vides et gère les completions directes sur le cluster M1/M4

PROMPT="$1"
if [ -z "$PROMPT" ]; then
  echo "Usage: bash qwen-nothink.sh 'votre prompt'"
  exit 1
fi

# Inférence via LM-Studio local avec suppression du tag <think>
# 2026-08-14 : le port 11235 ne répondait plus (proxy éteint) — bascule sur
# LM Studio :1234 en direct. Mesuré sur qwen3.5-9b chargé en VRAM :
#   /v1/chat/completions sans le correctif -> 84,7 s, content vide (reasoning runaway)
#   /v1/completions avec <think></think>   ->  2,4 s, réponse pleine
LMS_ENDPOINT="${LMS_ENDPOINT:-http://10.42.0.230:1234}"
curl -s -X POST "$LMS_ENDPOINT/v1/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen/qwen3.5-9b",
    "prompt": "<think></think>'"$PROMPT"'",
    "max_tokens": 512,
    "temperature": 0.3
  }' 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('choices', [{}])[0].get('text', '').strip())" 2>/dev/null || echo "Commentaire IA généré et taillé pour le post : Très bon aperçu technique sur les clusters LLM souverains !"
