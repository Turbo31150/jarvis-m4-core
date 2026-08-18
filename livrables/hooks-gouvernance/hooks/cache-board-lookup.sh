#!/usr/bin/env bash
# cache-board-lookup.sh — hook UserPromptSubmit : SQL AVANT inférence (règle 0-token).
# Cherche dans la board FTS5 (264k chunks souverains) des extraits pertinents au
# prompt et les injecte en additionalContext. AUCUNE inférence — lecture SQLite pure.
# Fail-safe absolu : toute erreur → '{}' + exit 0 (ne bloque jamais le prompt).
set -uo pipefail

DB="/storage/m1-mirror/databases/board.db"
MAX_HITS=3
MIN_MOTS=2

emit_empty() { echo '{}'; exit 0; }

[ -r "$DB" ] || emit_empty
command -v sqlite3 >/dev/null 2>&1 || emit_empty
command -v jq >/dev/null 2>&1 || emit_empty

# 1. Lire le prompt depuis le JSON stdin
INPUT="$(cat 2>/dev/null)" || emit_empty
PROMPT="$(printf '%s' "$INPUT" | jq -r '.prompt // .user_prompt // empty' 2>/dev/null)" || emit_empty
[ -n "$PROMPT" ] || emit_empty

# 2. Construire une requête FTS5 SÛRE : mots alphanumériques ≥4 lettres, dédupliqués,
#    chacun quoté, joints par OR. (Évite l'injection de syntaxe FTS5.)
MOTS="$(printf '%s' "$PROMPT" \
  | tr '[:upper:]' '[:lower:]' \
  | tr -cs 'a-zàâäéèêëïîôöùûüç0-9' '\n' \
  | awk 'length($0)>=4' \
  | grep -vE '^(avec|pour|dans|comme|cette|leur|elle|nous|vous|alors|donc|mais|plus|tout|tous|fait|faire|peux|veux|https|http|www)$' \
  | sort -u | head -8)"
NB=$(printf '%s\n' "$MOTS" | grep -c . || echo 0)
[ "$NB" -ge "$MIN_MOTS" ] || emit_empty

# Join en '"w1" OR "w2" OR ...' (paste -d ne gère qu'UN caractère → awk).
FTS=$(printf '%s\n' "$MOTS" | awk 'NF{q=q (q?" OR ":"") "\"" $0 "\""} END{print q}')
[ -n "$FTS" ] || emit_empty

# 3. Recherche FTS5 (lecture seule, immuable, timeout court)
RES="$(timeout 5 sqlite3 -separator ' — ' "file:${DB}?mode=ro&immutable=1" \
  "SELECT c.domain_id, substr(replace(f.text,char(10),' '),1,220)
     FROM chunks_fts f JOIN chunks c ON c.rowid = f.rowid
    WHERE chunks_fts MATCH '${FTS}'
      AND f.text NOT LIKE '%queue-operation%'
      AND f.text NOT LIKE '%sessionId%'
      AND f.text NOT LIKE '%\"timestamp\"%'
      AND length(f.text) > 80
    ORDER BY rank LIMIT ${MAX_HITS};" 2>/dev/null)" || emit_empty
[ -n "$RES" ] || emit_empty

# 4. Injecter en contexte (transparence : source board, 0-token)
CTX="📚 Contexte board local (souverain, 0-token) — extraits pertinents au prompt :\n${RES}"
jq -cn --arg c "$CTX" \
  '{hookSpecificOutput:{hookEventName:"UserPromptSubmit",additionalContext:$c}}' 2>/dev/null \
  || emit_empty
exit 0
