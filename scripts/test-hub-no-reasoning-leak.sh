#!/usr/bin/env bash
# Test régression : le hub 18800 ne doit PAS fuir le reasoning brut (petit max_tokens).
# ÉCHOUE si la réponse servie contient des marqueurs de reasoning.
Q='{"model":"auto","messages":[{"role":"user","content":"Dis juste: PRET"}],"max_tokens":64}'
R=$(curl -s -m 60 http://127.0.0.1:18800/v1/chat/completions -H 'Content-Type: application/json' -d "$Q")
TXT=$(echo "$R" | python3 -c 'import sys,json;print(json.load(sys.stdin)["choices"][0]["message"]["content"])' 2>/dev/null)
echo "servi: [$TXT]"
if echo "$TXT" | grep -qiE "Thinking Process|Okay, the user|Let me|reasoning|analyze the|the user (just|wants|said)"; then
  echo "❌ FAIL : fuite de reasoning dans la réponse"; exit 1
elif [ -z "$TXT" ]; then
  echo "❌ FAIL : réponse vide"; exit 1
else
  echo "✅ PASS : réponse propre, pas de fuite"; exit 0
fi
