#!/bin/bash
# gemini-route.sh — Routage fichier simple : ENTRÉE → Gemini (OAuth) → SORTIE,
# avec fallback LOCAL 0-token (M1 LM Studio :1234) si Gemini est en quota/erreur.
#
# Usages :
#   gemini-route.sh <fichier_in> <fichier_out>      # fichiers partagés
#   echo "prompt" | gemini-route.sh                 # stdin → stdout
#   gemini-route.sh --watch <dir>                   # démon : *.in → *.out
#
# Sortie : le texte de la réponse (rien d'autre sur stdout). Route utilisée sur stderr.
set -uo pipefail

M1="${M1_HOST:-192.168.0.10}"           # LM Studio local, 0 token
# gpt-oss-20b : met la réponse dans .content (qwen3 la noie dans reasoning_content → inexploitable)
M1_MODEL="${M1_MODEL:-openai/gpt-oss-20b}"
GMODEL="${GEMINI_MODEL:-gemini-3.7-flash}"
GBIN="$HOME/.npm-global/bin/gemini"

_local() {  # fallback 0-token via M1
  local p="$1"
  local payload
  # enable_thinking:false → qwen3 met la réponse dans content (sinon tout part dans
  # reasoning_content et content reste vide). On récupère quand même reasoning en secours.
  payload=$(jq -n --arg m "$M1_MODEL" --arg c "$p" \
    '{model:$m,messages:[{role:"user",content:$c}],stream:false,max_tokens:1024}')
  curl -s --max-time 90 "http://$M1:1234/v1/chat/completions" \
    -H 'Content-Type: application/json' -d "$payload" 2>/dev/null \
    | jq -r '.choices[0].message.content // empty' 2>/dev/null
}

# ── OMBRE : journalisation + scoring + feedback (boucle Lumière/Ombre) ──────────
DB="${ROUTE_DB:-$HOME/.jarvis/route.db}"
GEMINI_SKIP_MIN="${GEMINI_SKIP_MIN:-30}"   # feedback : si Gemini quota-KO il y a <30min → on saute

_db_init() {
  mkdir -p "$(dirname "$DB")"
  sqlite3 "$DB" "CREATE TABLE IF NOT EXISTS routes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER, route TEXT, status TEXT, dur_ms INTEGER,
    prompt_len INTEGER, out_len INTEGER);" 2>/dev/null
}
_log() {  # $1=route $2=status $3=dur_ms $4=plen $5=olen
  sqlite3 "$DB" "INSERT INTO routes(ts,route,status,dur_ms,prompt_len,out_len)
    VALUES($(date +%s),'$1','$2',${3:-0},${4:-0},${5:-0});" 2>/dev/null
}
_gemini_blocked_recently() {  # FEEDBACK : Gemini a-t-il été quota-KO récemment ?
  local n
  n=$(sqlite3 "$DB" "SELECT COUNT(*) FROM routes
    WHERE route='gemini' AND status='quota'
    AND ts > $(date +%s) - ${GEMINI_SKIP_MIN}*60;" 2>/dev/null)
  [ "${n:-0}" -gt 0 ]
}

route() {  # $1 = prompt ; imprime la réponse (LUMIÈRE) ; log+score (OMBRE)
  _db_init
  local prompt="$1" ans t0 dur plen="${#1}"
  # FEEDBACK (boucle) : sauter Gemini s'il était quota-bloqué récemment → gagne les 45s
  if ! _gemini_blocked_recently; then
    t0=$(date +%s%3N)
    ans=$(unset GEMINI_API_KEY; timeout 45 "$GBIN" -m "$GMODEL" -p "$prompt" 2>/dev/null \
          | grep -vE "metricReader|Ripgrep|deprecated" )
    dur=$(( $(date +%s%3N) - t0 ))
    if [ -n "$ans" ] && ! printf '%s' "$ans" | grep -qiE "quota|error when talking|API key not valid"; then
      _log gemini ok "$dur" "$plen" "${#ans}"
      echo "[route=gemini ${dur}ms]" >&2; printf '%s\n' "$ans"; return 0
    fi
    _log gemini quota "$dur" "$plen" 0   # OMBRE : marque le quota → feedback futur
  else
    echo "[feedback: Gemini quota-KO <${GEMINI_SKIP_MIN}min → saut direct local]" >&2
  fi
  # Fallback local M1 (0 token)
  t0=$(date +%s%3N)
  ans=$(_local "$prompt")
  dur=$(( $(date +%s%3N) - t0 ))
  if [ -n "$ans" ]; then
    _log local-M1 ok "$dur" "$plen" "${#ans}"
    echo "[route=local-M1 ${dur}ms]" >&2; printf '%s\n' "$ans"; return 0
  fi
  _log local-M1 error "$dur" "$plen" 0
  echo "[ERREUR: Gemini ET M1 injoignables]" >&2; return 1
}

_analyze() {  # SCORING : lit l'Ombre, sort le feedback lisible
  _db_init
  echo "=== Routeur Lumière/Ombre — scoring ($DB) ==="
  sqlite3 -column -header "$DB" "SELECT route, status,
    COUNT(*) n, ROUND(AVG(dur_ms)) dur_moy_ms, ROUND(AVG(out_len)) out_moy
    FROM routes GROUP BY route,status ORDER BY n DESC;" 2>/dev/null
  local total gq
  total=$(sqlite3 "$DB" "SELECT COUNT(*) FROM routes;" 2>/dev/null)
  gq=$(sqlite3 "$DB" "SELECT COUNT(*) FROM routes WHERE route='gemini' AND status='quota';" 2>/dev/null)
  echo "--- feedback : $total actions · Gemini quota-KO ${gq:-0}× · saut auto si <${GEMINI_SKIP_MIN}min ---"
}

# --- modes ---
if [ "${1:-}" = "--analyze" ] || [ "${1:-}" = "--score" ]; then
  _analyze; exit 0
elif [ "${1:-}" = "--watch" ]; then
  DIR="${2:-$HOME/.jarvis/gemini-route}"; mkdir -p "$DIR"
  echo "watch $DIR : dépose un *.in → lit le *.out correspondant" >&2
  while true; do
    for f in "$DIR"/*.in; do
      [ -e "$f" ] || continue
      out="${f%.in}.out"
      route "$(cat "$f")" > "$out" 2>>"$DIR/route.log"
      mv "$f" "$f.done"
    done
    sleep 1
  done
elif [ -n "${1:-}" ] && [ -f "$1" ]; then
  OUT="${2:-/dev/stdout}"
  route "$(cat "$1")" > "$OUT"
else
  # stdin → stdout (ou arg direct)
  if [ -n "${1:-}" ]; then route "$1"; else route "$(cat)"; fi
fi
