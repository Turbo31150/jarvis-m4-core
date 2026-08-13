#!/bin/bash
# antigravity-ask.sh — Accès direct API Google Cloud Code (Antigravity IDE)
# Modèles Gemini (generateContent) + Claude + GPT-OSS (generateChat)
# Quota SÉPARÉ de gemini-cli — fallback quand les autres sont épuisés
#
# Usage: antigravity-ask.sh "question" [--model ID|NAME] [--max N]
#
# Models disponibles:
#   Gemini  : gemini-3.1-pro-preview, gemini-3-pro-preview, gemini-3.1-flash-lite-preview
#             gemini-3-flash-preview, gemini-2.5-pro, gemini-2.5-flash
#   Claude  : claude-sonnet (4.6 Thinking, model_config_id=1035)
#             claude-opus   (4.6 Thinking, model_config_id=1026)
#   GPT-OSS : gpt-oss       (120B Medium,  model_config_id=342)
#
# Credentials Antigravity OAuth (public client ID dans le bundle gemini-cli)
CLIENT_ID="1071006060591-tmhssin2h21lcre235vtolojh4g403ep.apps.googleusercontent.com"
# CLIENT_SECRET externalisé -> ~/jarvis/.secrets/cluster-secrets.env (méga-audit 2026-06-11 R1)
[ -f "$HOME/jarvis/.secrets/cluster-secrets.env" ] && . "$HOME/jarvis/.secrets/cluster-secrets.env"
: "${CLIENT_SECRET:?manque dans ~/jarvis/.secrets/cluster-secrets.env}"
PROJECT_ID="supple-catfish-pqk61"
ENDPOINT_GEMINI="https://cloudcode-pa.googleapis.com/v1internal:generateContent"
ENDPOINT_CHAT="https://cloudcode-pa.googleapis.com/v1internal:generateChat"
STATE_DB="$HOME/.config/Antigravity/User/globalStorage/state.vscdb"
TOKEN_CACHE="/tmp/antigravity-token.cache"

# Modèles Gemini par ordre de préférence (generateContent endpoint)
GEMINI_MODELS=(
  "gemini-3.1-pro-preview"
  "gemini-3-pro-preview"
  "gemini-3.1-flash-lite-preview"
  "gemini-3-flash-preview"
  "gemini-2.5-pro"
  "gemini-2.5-flash"
)

# Modèles non-Gemini par ordre de préférence (generateChat endpoint, model_config_id)
# Format: "nom:model_config_id"
CHAT_MODELS=(
  "claude-sonnet:1035"
  "gpt-oss:342"
  "claude-opus:1026"
)

MODEL=""
MAX=4096
ARGS=()

# Parser les args (flags n'importe où)
while [[ $# -gt 0 ]]; do
  case "$1" in
    --model) MODEL="$2"; shift 2 ;;
    --max)   MAX="$2"; shift 2 ;;
    --*)     shift ;;
    *)       ARGS+=("$1"); shift ;;
  esac
done

PROMPT="${ARGS[*]}"
[[ -t 0 ]] || PROMPT="$(cat)
$PROMPT"
[[ -z "$PROMPT" ]] && { echo "Usage: antigravity-ask.sh \"question\"" >&2; exit 1; }

# === Obtenir le refresh token depuis state.vscdb ===
get_refresh_token() {
  python3 -c "
import sqlite3, base64, re, sys
try:
    conn = sqlite3.connect('$STATE_DB')
    cur = conn.cursor()
    cur.execute('SELECT value FROM ItemTable WHERE key = \"antigravityUnifiedStateSync.oauthToken\"')
    row = cur.fetchone()
    conn.close()
    if not row: sys.exit(1)
    outer = base64.b64decode(row[0])
    all_text = outer.decode('utf-8', errors='replace')
    for m in re.finditer(r'[A-Za-z0-9+/]{40,}={0,2}', all_text):
        try:
            dec = base64.b64decode(m.group() + '===')
            ds = dec.decode('utf-8', errors='replace')
            rt = re.search(r'1//[A-Za-z0-9_\-]{20,}', ds)
            if rt:
                print(rt.group())
                sys.exit(0)
        except: pass
    sys.exit(1)
except Exception as e:
    sys.exit(1)
" 2>/dev/null
}

# === Obtenir ou rafraîchir le token d'accès ===
get_access_token() {
  if [[ -f "$TOKEN_CACHE" ]]; then
    local cached_time
    cached_time=$(stat -c %Y "$TOKEN_CACHE" 2>/dev/null || echo 0)
    local now; now=$(date +%s)
    if [[ $((now - cached_time)) -lt 3300 ]]; then
      cat "$TOKEN_CACHE"
      return 0
    fi
  fi

  local refresh_token
  refresh_token=$(get_refresh_token)
  [[ -z "$refresh_token" ]] && { echo "✘ Impossible d'obtenir le refresh token Antigravity" >&2; return 1; }

  local response token
  response=$(curl -s -m 10 -X POST "https://oauth2.googleapis.com/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}&refresh_token=${refresh_token}&grant_type=refresh_token" 2>/dev/null)
  token=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)

  if [[ -z "$token" ]]; then
    echo "✘ Échec refresh token Antigravity" >&2
    return 1
  fi

  echo "$token" > "$TOKEN_CACHE"
  chmod 600 "$TOKEN_CACHE"
  echo "$token"
}

# === Appel generateContent (Gemini) ===
call_gemini() {
  local model="$1" token="$2" payload result

  payload=$(python3 -c "
import json, sys
prompt = sys.argv[1]
model = sys.argv[2]
project = sys.argv[3]
max_tok = int(sys.argv[4])
req = {
    'model': model,
    'project': project,
    'user_prompt_id': 'ag-ask-' + model[:10],
    'request': {
        'contents': [{'parts': [{'text': prompt}], 'role': 'user'}],
        'generationConfig': {'maxOutputTokens': max_tok, 'temperature': 0.2}
    }
}
print(json.dumps(req))
" "$PROMPT" "$model" "$PROJECT_ID" "$MAX" 2>/dev/null)

  result=$(curl -s -m 120 -X POST "$ENDPOINT_GEMINI" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d "$payload" 2>/dev/null)

  python3 -c "
import json, sys
d = json.load(sys.stdin)
e = d.get('error', {})
if e:
    code = e.get('code', 0)
    if code == 429:
        print('QUOTA_EXHAUSTED', file=sys.stderr); sys.exit(2)
    elif code == 404:
        print('MODEL_NOT_FOUND', file=sys.stderr); sys.exit(3)
    else:
        print(f'ERROR {code}: {e.get(\"message\",\"\")}', file=sys.stderr); sys.exit(1)
r = d.get('response', d)
candidates = r.get('candidates', [])
if candidates:
    parts = candidates[0].get('content', {}).get('parts', [])
    text = ''.join(p.get('text','') for p in parts)
    print(text); sys.exit(0)
sys.exit(1)
" <<< "$result"
  return $?
}

# === Appel generateChat (Claude / GPT-OSS) ===
call_chat() {
  local model_config_id="$1" token="$2" payload result

  payload=$(python3 -c "
import json, sys
prompt = sys.argv[1]; model_config_id = sys.argv[2]; project = sys.argv[3]
print(json.dumps({'model_config_id': model_config_id, 'project': project, 'history': [{'author': 'user', 'content': prompt}]}))
" "$PROMPT" "$model_config_id" "$PROJECT_ID" 2>/dev/null)

  result=$(curl -s -m 120 -X POST "$ENDPOINT_CHAT" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d "$payload" 2>/dev/null)

  python3 -c "
import json, sys
d = json.load(sys.stdin)
e = d.get('error', {})
if e:
    code = e.get('code', 0)
    if code == 429:
        print('QUOTA_EXHAUSTED', file=sys.stderr); sys.exit(2)
    elif code == 404:
        print('MODEL_NOT_FOUND', file=sys.stderr); sys.exit(3)
    else:
        print(f'ERROR {code}: {e.get(\"message\",\"\")}', file=sys.stderr); sys.exit(1)
text = d.get('markdown', '')
if text:
    print(text); sys.exit(0)
sys.exit(1)
" <<< "$result"
  return $?
}

# === Résoudre l'alias de modèle ===
resolve_model_alias() {
  local m="$1"
  case "$m" in
    claude|claude-sonnet|sonnet) echo "chat:1035" ;;
    claude-opus|opus)             echo "chat:1026" ;;
    gpt-oss|gpt|oss)              echo "chat:342" ;;
    *)
      if [[ "$m" =~ ^[0-9]+$ ]]; then
        echo "chat:$m"
      else
        echo "gemini:$m"
      fi
      ;;
  esac
}

# === Main ===
TOKEN=$(get_access_token)
[[ -z "$TOKEN" ]] && exit 1

# Si modèle spécifié, utiliser directement
if [[ -n "$MODEL" ]]; then
  resolved=$(resolve_model_alias "$MODEL")
  type="${resolved%%:*}"
  id="${resolved##*:}"
  if [[ "$type" == "chat" ]]; then
    RESULT=$(call_chat "$id" "$TOKEN" 2>/tmp/ag_err.txt)
    EXIT=$?
  else
    RESULT=$(call_gemini "$id" "$TOKEN" 2>/tmp/ag_err.txt)
    EXIT=$?
  fi
  if [[ $EXIT -eq 0 && -n "$RESULT" ]]; then
    echo "$RESULT"; exit 0
  fi
  exit $EXIT
fi

# Sinon, essayer Gemini d'abord, puis Claude/GPT-OSS
for m in "${GEMINI_MODELS[@]}"; do
  RESULT=$(call_gemini "$m" "$TOKEN" 2>/tmp/ag_err.txt)
  EXIT=$?
  if [[ $EXIT -eq 0 && -n "$RESULT" ]]; then
    echo "$RESULT"; exit 0
  fi
  ERR=$(cat /tmp/ag_err.txt 2>/dev/null)
  [[ "$ERR" == "MODEL_NOT_FOUND" || "$ERR" == "QUOTA_EXHAUSTED" ]] && continue
  echo "✘ Antigravity Gemini error sur $m: $ERR" >&2
  break
done

# Fallback sur les modèles chat (Claude / GPT-OSS)
for entry in "${CHAT_MODELS[@]}"; do
  name="${entry%%:*}"
  id="${entry##*:}"
  RESULT=$(call_chat "$id" "$TOKEN" 2>/tmp/ag_err.txt)
  EXIT=$?
  if [[ $EXIT -eq 0 && -n "$RESULT" ]]; then
    echo "$RESULT"; exit 0
  fi
  ERR=$(cat /tmp/ag_err.txt 2>/dev/null)
  [[ "$ERR" == "QUOTA_EXHAUSTED" || "$ERR" == "MODEL_NOT_FOUND" ]] && continue
  echo "✘ Antigravity chat error sur $name: $ERR" >&2
done

echo "✘ Tous les modèles Antigravity épuisés ou indisponibles" >&2
exit 2
