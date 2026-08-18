#!/usr/bin/env bash
# gen-content-kit.sh — génère un kit de contenu multi-format (LinkedIn, tweets,
# carrousel, email) pour un sujet/offre donné. 100% cascade LOCALE 0-token.
# Usage : gen-content-kit.sh "sujet ou offre" ["cible/angle optionnel"]
# Sortie : ~/jarvis/wbs/drafts/kit-<slug>-<date>.md  (prêt pour push-draft Telegram)
#
# Cascade (skill « cascade parfaite ») : M6 LM Studio si un modèle est CHARGÉ →
# sinon Ollama local qwen2.5:7b → sinon gemma3:4b. Jamais d'IA facturée. On-demand.
set -uo pipefail

SUJET="${1:-}"
ANGLE="${2:-entrepreneurs et PME qui veulent gagner du temps}"
[ -z "$SUJET" ] && { echo "usage: $0 \"<sujet/offre>\" [\"<cible/angle>\"]" >&2; exit 1; }

OUT_DIR="$HOME/jarvis/wbs/drafts"; mkdir -p "$OUT_DIR"
SLUG=$(printf '%s' "$SUJET" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//;s/-$//' | cut -c1-40)
DATE=$(date +%Y%m%d)
OUT="$OUT_DIR/kit-${SLUG}-${DATE}.md"
M6="http://10.42.0.230:1234"; OL="http://127.0.0.1:11434"

# --- Choix backend 0-token (transparence) ---
BACKEND=""; MODE=""
M6_LOADED=$(curl -s -m 4 "$M6/api/v0/models" 2>/dev/null | python3 -c "import sys,json;print(next((m['id'] for m in json.load(sys.stdin)['data'] if m.get('state')=='loaded' and 'embed' not in m['id']),''))" 2>/dev/null || true)
if [ -n "$M6_LOADED" ]; then
  BACKEND="M6:$M6_LOADED"; MODE="m6"
elif curl -s -m 3 "$OL/api/tags" >/dev/null 2>&1; then
  if curl -s -m 3 "$OL/api/tags" | grep -q 'qwen2.5:7b'; then BACKEND="ollama:qwen2.5:7b"; else BACKEND="ollama:gemma3:4b"; fi
  MODE="ollama"
else
  echo "⚠ Aucun backend local 0-token disponible (M6 déchargé + Ollama down)." >&2; exit 3
fi
OL_MODEL="${BACKEND#ollama:}"

# --- Fonction d'inférence 0-token (fail-safe) ---
gen() { # $1=prompt  $2=max_tokens
  local prompt="$1" maxtok="${2:-400}" out=""
  if [ "$MODE" = "m6" ]; then
    out=$(curl -s -m 120 "$M6/v1/chat/completions" -H "Content-Type: application/json" \
      -d "$(python3 -c "import json,sys;print(json.dumps({'model':sys.argv[1],'messages':[{'role':'user','content':sys.argv[2]}],'max_tokens':int(sys.argv[3]),'temperature':0.75}))" "$M6_LOADED" "$prompt" "$maxtok")" \
      | python3 -c "import sys,json;print(json.load(sys.stdin)['choices'][0]['message']['content'].strip())" 2>/dev/null || true)
  else
    out=$(curl -s -m 120 "$OL/api/generate" \
      -d "$(python3 -c "import json,sys;print(json.dumps({'model':sys.argv[1],'prompt':sys.argv[2],'stream':False,'options':{'temperature':0.75,'num_predict':int(sys.argv[3])}}))" "$OL_MODEL" "$prompt" "$maxtok")" \
      | python3 -c "import sys,json;print(json.load(sys.stdin).get('response','').strip())" 2>/dev/null || true)
  fi
  printf '%s' "${out:-（génération vide, réessaie）}"
}

CTX="Contexte : $SUJET. Cible : $ANGLE. Ton concret, orienté bénéfice, français, sans superlatifs creux ni jargon."

echo "→ Génération kit contenu 0-token ($BACKEND) pour : $SUJET" >&2
{
  echo "# Kit de contenu — $SUJET"
  echo "> Généré 0-token via $BACKEND le $(date +%F). Brouillon à relire avant publication."
  echo; echo "## 📱 POST LINKEDIN"
  gen "$CTX Écris UN post LinkedIn de 150 mots : accroche forte, 3 bénéfices concrets, 1 appel à l'action, 2 émojis max, 3 hashtags." 380
  echo; echo "## 🐦 3 TWEETS"
  gen "$CTX Écris 3 tweets numérotés (max 260 caractères chacun), 3 angles différents, 1 hashtag chacun." 320
  echo; echo "## 🖼️ CARROUSEL (5 slides)"
  gen "$CTX Écris un carrousel 5 slides format 'Slide N : TITRE — phrase'. Slide 1 accroche, 2-4 bénéfices, 5 appel à l'action." 350
  echo; echo "## ✉️ EMAIL"
  gen "$CTX Écris un email court : 'Objet : ...' puis 3 lignes de corps puis une signature (Franck)." 300
} > "$OUT"

echo "$OUT"
