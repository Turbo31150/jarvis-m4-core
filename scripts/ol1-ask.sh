#!/usr/bin/env bash
# ol1-ask.sh — 0-token via OL1 (Ollama local). Cold-load safe. Fallback M1/M2 si dispo.
# Usage : ol1-ask.sh "question" [modele]   (defaut gemma3:4b ; alt qwen2.5:7b)
Q="$1"; M="${2:-gemma3:4b}"
curl -s -m180 http://127.0.0.1:11434/api/generate \
  -d "$(python3 -c "import json,sys; print(json.dumps({'model':'$M','prompt':sys.argv[1],'stream':False,'options':{'num_predict':512,'temperature':0.7}}))" "$Q")" \
  2>/dev/null | python3 -c "import sys,json
try: print(json.load(sys.stdin).get('response','').strip())
except: sys.exit(1)"
