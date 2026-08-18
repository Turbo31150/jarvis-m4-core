#!/usr/bin/env bash
# ask-cascade.sh — connecteur d'inférence 0-token UNIFIÉ, fallback ordonné.
# Usage : ask-cascade.sh "<prompt>" [max_tokens]
# Essaie les backends dans l'ordre du moins cher/plus fiable au plus lourd,
# s'arrête au premier qui répond. Affiche le backend utilisé sur stderr.
# Aucun backend facturé. Aucun secret en clair (lus depuis env/coffre).
set -uo pipefail

PROMPT="${1:-}"; MAXTOK="${2:-500}"
[ -z "$PROMPT" ] && { echo "usage: $0 \"<prompt>\" [max_tokens]" >&2; exit 1; }
OL="http://127.0.0.1:11434"; M6="http://10.42.0.230:1234"

ok() { [ -n "${1:-}" ] && [ "${1}" != "null" ] && [ "$(printf '%s' "$1" | wc -c)" -gt 3 ]; }

# --- 1) Ollama local qwen2.5:7b (fiable, testé) ---
if curl -s -m 3 "$OL/api/tags" 2>/dev/null | grep -q 'qwen2.5:7b'; then
  R=$(curl -s -m 100 "$OL/api/generate" -d "$(python3 -c "import json,sys;print(json.dumps({'model':'qwen2.5:7b','prompt':sys.argv[1],'stream':False,'options':{'num_predict':int(sys.argv[2]),'temperature':0.7}}))" "$PROMPT" "$MAXTOK")" 2>/dev/null | python3 -c "import sys,json;print(json.load(sys.stdin).get('response','').strip())" 2>/dev/null || true)
  if ok "$R"; then echo "[backend=ollama:qwen2.5:7b]" >&2; printf '%s\n' "$R"; exit 0; fi
fi

# --- 2) M6 LM Studio SI un modèle chat est déjà chargé (pas de JIT lent) ---
M6M=$(curl -s -m 4 "$M6/api/v0/models" 2>/dev/null | python3 -c "import sys,json;print(next((m['id'] for m in json.load(sys.stdin)['data'] if m.get('state')=='loaded' and 'embed' not in m['id']),''))" 2>/dev/null || true)
if [ -n "$M6M" ]; then
  R=$(curl -s -m 120 "$M6/v1/chat/completions" -H "Content-Type: application/json" -d "$(python3 -c "import json,sys;print(json.dumps({'model':sys.argv[1],'messages':[{'role':'user','content':sys.argv[2]}],'max_tokens':int(sys.argv[3]),'temperature':0.7}))" "$M6M" "$PROMPT" "$MAXTOK")" 2>/dev/null | python3 -c "import sys,json;print(json.load(sys.stdin)['choices'][0]['message']['content'].strip())" 2>/dev/null || true)
  if ok "$R"; then echo "[backend=M6:$M6M]" >&2; printf '%s\n' "$R"; exit 0; fi
fi

# --- 3) gemma3:4b local (léger, dernier recours local) ---
if curl -s -m 3 "$OL/api/tags" 2>/dev/null | grep -q 'gemma3:4b'; then
  R=$(curl -s -m 90 "$OL/api/generate" -d "$(python3 -c "import json,sys;print(json.dumps({'model':'gemma3:4b','prompt':sys.argv[1],'stream':False,'options':{'num_predict':int(sys.argv[2])}}))" "$PROMPT" "$MAXTOK")" 2>/dev/null | python3 -c "import sys,json;print(json.load(sys.stdin).get('response','').strip())" 2>/dev/null || true)
  if ok "$R"; then echo "[backend=ollama:gemma3:4b]" >&2; printf '%s\n' "$R"; exit 0; fi
fi

echo "[backend=AUCUN] tous les backends 0-token sont muets (M6 déchargé, Ollama down)." >&2
exit 3
