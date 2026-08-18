#!/usr/bin/env bash
# sql-first.sh — Cahier des charges Pamerys/M4 appliqué.
# Ordre OBLIGATOIRE du moins cher au plus cher :
#   1) SQL d'abord (cache des réponses déjà calculées)
#   2) 0 token (cascade Ollama local+cloud via lm-ask.sh) avec profil injecté
#   3) compute local : seulement si cache-miss ET température sous la cible
# Stocke chaque réponse en base => la prochaine fois = cache hit (0 watt, 0 token).
#
# Usage : sql-first.sh "ta question"
#         sql-first.sh --stats          # statistiques du cache
#         sql-first.sh --no-store "..."  # ne pas mémoriser
set -uo pipefail
trap '' USR1 SIGUSR1   # la dictée vocale envoie des SIGUSR1 (cf m4-dictee-vocale)

DB="$HOME/IA/Core/jarvis/db/llm_cache.db"
PROFILE="$HOME/jarvis/profile-pamerys.md"
LM="$HOME/jarvis/scripts/lm-ask.sh"
CIBLE=82   # °C : au-dessus, pas d'inférence LOCALE (cf gouverneur thermique)

mkdir -p "$(dirname "$DB")"
sqlite3 "$DB" "CREATE TABLE IF NOT EXISTS cache(
  key TEXT PRIMARY KEY, question TEXT, answer TEXT,
  backend TEXT, ts TEXT DEFAULT (datetime('now')), hits INTEGER DEFAULT 0);" 2>/dev/null

# --- statistiques ---
if [ "${1:-}" = "--stats" ]; then
  echo "=== Cache LLM ($DB) ==="
  sqlite3 -box "$DB" "SELECT COUNT(*) AS entrees, COALESCE(SUM(hits),0) AS hits_total,
    COALESCE(SUM(hits),0) AS calculs_evites FROM cache;"
  sqlite3 -box "$DB" "SELECT substr(question,1,40) AS question, backend, hits FROM cache ORDER BY hits DESC LIMIT 5;"
  exit 0
fi

STORE=1
[ "${1:-}" = "--no-store" ] && { STORE=0; shift; }
Q="$*"
[ -z "$Q" ] && { echo "Usage: sql-first.sh \"question\"" >&2; exit 2; }

# clé = hash de la question normalisée (minuscules, espaces compressés)
NORM=$(printf '%s' "$Q" | tr '[:upper:]' '[:lower:]' | tr -s ' ' | sed 's/^ *//;s/ *$//')
KEY=$(printf '%s' "$NORM" | sha256sum | cut -c1-32)

# --- 1) SQL D'ABORD ---
HIT=$(sqlite3 "$DB" "SELECT answer FROM cache WHERE key='$KEY';" 2>/dev/null)
if [ -n "$HIT" ]; then
  sqlite3 "$DB" "UPDATE cache SET hits=hits+1 WHERE key='$KEY';" 2>/dev/null
  echo "[SQL-CACHE] (0 token, 0 watt)"
  echo "$HIT"
  exit 0
fi

# --- garde-fou thermique avant tout calcul local ---
T=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader 2>/dev/null | head -1)
T=${T:-0}
PREFER_CLOUD=""
if [ "$T" -ge "$CIBLE" ] 2>/dev/null; then
  echo "[THERMAL] GPU ${T}C >= cible ${CIBLE}C -> on évite l'inférence locale, cascade cloud uniquement" >&2
  PREFER_CLOUD="--cloud"
fi

# --- 2) 0 TOKEN : cascade Ollama local+cloud, profil Pamerys injecté ---
CTX=""
[ -f "$PROFILE" ] && CTX="Contexte utilisateur (réponds en conséquence):\n$(cat "$PROFILE")\n\nQuestion: "
ANS=""
if [ -x "$LM" ]; then
  ANS=$(printf '%b%s' "$CTX" "$Q" | "$LM" $PREFER_CLOUD 2>/dev/null)
fi

# --- 2bis) FALLBACK OL1 EN CPU (num_gpu:0) ---
# Seul chemin fiable sur M4 isolé : cluster M1/M2 down, cloud cassé,
# VRAM saturée (LM Studio) => Ollama local en CPU pur ignore VRAM + GPU chaud.
OL1="http://127.0.0.1:11434"
FB_MODEL="${SQLFIRST_OL1_MODEL:-gemma3:4b}"
if [ -z "$ANS" ] && curl -s -m3 -o /dev/null "$OL1/api/tags" 2>/dev/null; then
  echo "[FALLBACK OL1/CPU] cascade vide -> $FB_MODEL en CPU pur" >&2
  PROMPT=$(printf '%b%s' "$CTX" "$Q")
  ANS=$(curl -s -m180 "$OL1/api/generate" \
    --data-binary "$(python3 -c "import json,sys; print(json.dumps({'model':'$FB_MODEL','prompt':sys.stdin.read(),'stream':False,'options':{'num_predict':400,'temperature':0.4,'num_gpu':0}}))" <<<"$PROMPT")" \
    2>/dev/null | python3 -c "import sys,json
try: print(json.load(sys.stdin).get('response','').strip())
except: pass")
  [ -n "$ANS" ] && PREFER_CLOUD="-ol1cpu"
fi

[ -z "$ANS" ] && { echo "[ERREUR] tous les backends ont échoué (cluster down, cloud cassé, OL1 KO)" >&2; exit 4; }

# --- 3) stocker pour cache hit la prochaine fois ---
if [ "$STORE" = "1" ]; then
  ESC_Q=$(printf '%s' "$Q" | sed "s/'/''/g")
  ESC_A=$(printf '%s' "$ANS" | sed "s/'/''/g")
  sqlite3 "$DB" "INSERT OR REPLACE INTO cache(key,question,answer,backend,hits)
    VALUES('$KEY','$ESC_Q','$ESC_A','lm-ask${PREFER_CLOUD}',0);" 2>/dev/null
fi
echo "[LM 0-token${PREFER_CLOUD}] (mémorisé en SQL pour la prochaine fois)"
echo "$ANS"
