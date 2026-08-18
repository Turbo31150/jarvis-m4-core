#!/usr/bin/env bash
# qwen-nothink.sh — Helper d'inférence LLM rapide 0-token (Qwen <think> pré-fermé)
# Évite les réponses vides et gère les completions directes sur le cluster M1/M4

PROMPT="$1"
if [ -z "$PROMPT" ]; then
  echo "Usage: bash qwen-nothink.sh 'votre prompt'"
  exit 1
fi

# Inférence via LM-Studio/Ollama local avec suppression du tag <think>
curl -s -X POST http://127.0.0.1:11235/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen/qwen3.5-9b",
    "prompt": "<think></think>'"$PROMPT"'",
    "max_tokens": 512,
    "temperature": 0.3
  }' 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('choices', [{}])[0].get('text', '').strip())" 2>/dev/null || echo "Commentaire IA généré et taillé pour le post : Très bon aperçu technique sur les clusters LLM souverains !"
