#!/usr/bin/env bash
# repurpose.sh — « Repurpose 1 → 4 » : un post source → 4 formats prêts à relire.
#
#   1. LinkedIn (150-250 mots, ton pro)
#   2. X / Twitter (un tweet ≤ 280 caractères)
#   3. Script Reel / Short (30-45 s, découpage plan par plan)
#   4. Plan de carrousel Instagram (5-7 slides)
#
# Inférence 100 % LOCALE 0-token. AUCUNE publication, AUCUN envoi : l'outil
# produit uniquement des BROUILLONS locaux. La publication reste manuelle et
# passe par un pilote unique après validation (cf. docs/REPURPOSE-1-4.md).
#
# Usage :
#   repurpose.sh "<texte du post source>"
#   repurpose.sh -f chemin/vers/post.txt
#   echo "<texte>" | repurpose.sh
#
# Sortie : ~/jarvis/wbs/drafts/repurpose-<slug>-<horodatage>/
#            01-linkedin.md  02-twitter.md  03-reel-short.md
#            04-carousel-instagram.md  00-INDEX.md
#
# Cascade 0-token (réutilise la logique de gen-content-kit.sh + lm-ask.sh) :
#   M6 LM Studio si un modèle est CHARGÉ  →  Ollama qwen2.5:7b  →  gemma3:4b.
#   Jamais d'IA facturée au runtime. On-demand, fail-safe.
set -uo pipefail

# ---------------------------------------------------------------------------
# 1. Lecture de la source (argument, fichier -f, ou stdin)
# ---------------------------------------------------------------------------
SRC=""
if [ "${1:-}" = "-f" ]; then
  [ -n "${2:-}" ] && [ -r "$2" ] || { echo "repurpose.sh: fichier illisible: ${2:-<vide>}" >&2; exit 2; }
  SRC="$(cat "$2")"
elif [ -n "${1:-}" ]; then
  SRC="$1"
elif [ ! -t 0 ]; then
  SRC="$(cat)"
fi

if [ -z "${SRC//[[:space:]]/}" ]; then
  cat >&2 <<'EOF'
repurpose.sh: post source vide — rien à décliner.
usage: repurpose.sh "<texte du post>"   |   repurpose.sh -f post.txt   |   echo "<texte>" | repurpose.sh
EOF
  exit 2
fi

# ---------------------------------------------------------------------------
# 2. Chemins de sortie (dossier daté sous ~/jarvis/wbs/drafts/)
# ---------------------------------------------------------------------------
OUT_ROOT="$HOME/jarvis/wbs/drafts"
STAMP="$(date +%Y%m%d-%H%M%S)"
SLUG=$(printf '%s' "$SRC" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' \
        | sed 's/^-//;s/-$//' | cut -c1-40)
[ -z "$SLUG" ] && SLUG="post"
OUT_DIR="$OUT_ROOT/repurpose-${SLUG}-${STAMP}"
mkdir -p "$OUT_DIR" || { echo "repurpose.sh: impossible de créer $OUT_DIR" >&2; exit 4; }

# ---------------------------------------------------------------------------
# 3. Sélection du backend 0-token (transparence, on-demand)
# ---------------------------------------------------------------------------
M6="${M6_HOST:-http://<LLM_HOST>:1234}"
OL="${OLLAMA_URL:-http://127.0.0.1:11434}"
BACKEND=""; MODE=""; M6_MODEL=""; OL_MODEL=""

M6_MODEL=$(curl -s -m 4 "$M6/api/v0/models" 2>/dev/null | python3 -c \
  "import sys,json
try:
    d=json.load(sys.stdin)
    print(next((m['id'] for m in d.get('data',[]) if m.get('state')=='loaded' and 'embed' not in m['id']),''))
except Exception:
    print('')" 2>/dev/null || true)

if [ -n "$M6_MODEL" ]; then
  BACKEND="M6 LM Studio ($M6_MODEL)"; MODE="m6"
elif curl -s -m 3 "$OL/api/tags" >/dev/null 2>&1; then
  if curl -s -m 3 "$OL/api/tags" 2>/dev/null | grep -q 'qwen2.5:7b'; then
    OL_MODEL="qwen2.5:7b"
  elif curl -s -m 3 "$OL/api/tags" 2>/dev/null | grep -q 'gemma3:4b'; then
    OL_MODEL="gemma3:4b"
  else
    OL_MODEL="$(curl -s -m 3 "$OL/api/tags" 2>/dev/null | python3 -c \
      "import sys,json
try: print((json.load(sys.stdin).get('models') or [{}])[0].get('name',''))
except Exception: print('')" 2>/dev/null)"
  fi
  [ -z "$OL_MODEL" ] && { echo "repurpose.sh: Ollama joignable mais aucun modèle installé (ollama pull qwen2.5:7b)." >&2; exit 3; }
  BACKEND="Ollama local ($OL_MODEL)"; MODE="ollama"
else
  cat >&2 <<EOF
repurpose.sh: aucun backend IA local 0-token disponible.
  · M6 LM Studio ($M6) : aucun modèle chargé (charge un modèle côté LM Studio M6),
  · Ollama ($OL) : injoignable (démarre le service : systemctl --user start ollama, ou 'ollama serve').
Aucune IA facturée n'est utilisée en repli : relance quand un backend local répond.
EOF
  exit 3
fi

# ---------------------------------------------------------------------------
# 4. Fonction d'inférence 0-token (JSON échappé par json.dumps, fail-safe)
# ---------------------------------------------------------------------------
gen() { # $1=instruction  $2=max_tokens
  local instr="$1" maxtok="${2:-450}" out=""
  local prompt="Voici un post source à décliner :
---
$SRC
---
$instr
Réponds en français, uniquement le contenu demandé, sans commentaire ni préambule."

  if [ "$MODE" = "m6" ]; then
    # Parade reasoning-runaway qwen3.5 : /v1/completions avec <think></think> pré-fermé.
    out=$(PROMPT="$prompt" MODEL="$M6_MODEL" MAXTOK="$maxtok" python3 -c '
import json,os,sys
body=json.dumps({
  "model":os.environ["MODEL"],
  "prompt":("<|im_start|>user\n"+os.environ["PROMPT"]+"<|im_end|>\n"
            "<|im_start|>assistant\n<think></think>\n\n"),
  "temperature":0.7,"max_tokens":int(os.environ["MAXTOK"]),"stop":["<|im_end|>"],
})
sys.stdout.write(body)' | \
      curl -s --connect-timeout 3 --max-time 180 "$M6/v1/completions" \
        -H "Content-Type: application/json" \
        ${LM_API_KEY:+-H "Authorization: Bearer $LM_API_KEY"} \
        --data-binary @- 2>/dev/null | python3 -c '
import sys,json
try: print(((json.load(sys.stdin).get("choices") or [{}])[0]).get("text","").strip())
except Exception: print("")' 2>/dev/null || true)
  else
    out=$(PROMPT="$prompt" MODEL="$OL_MODEL" MAXTOK="$maxtok" python3 -c '
import json,os,sys
sys.stdout.write(json.dumps({
  "model":os.environ["MODEL"],"prompt":os.environ["PROMPT"],
  "stream":False,"options":{"temperature":0.7,"num_predict":int(os.environ["MAXTOK"])},
}))' | \
      curl -s --connect-timeout 3 --max-time 180 "$OL/api/generate" \
        -H "Content-Type: application/json" --data-binary @- 2>/dev/null | python3 -c '
import sys,json
try: print(json.load(sys.stdin).get("response","").strip())
except Exception: print("")' 2>/dev/null || true)
  fi
  printf '%s' "${out:-_(génération vide — backend surchargé ou modèle trop lent, relance)_}"
}

# ---------------------------------------------------------------------------
# 5. Génération des 4 variantes → 4 fichiers brouillons séparés
# ---------------------------------------------------------------------------
echo "→ Repurpose 1→4 (0-token via $BACKEND)" >&2
HEADER_NOTE="> BROUILLON généré 0-token via $BACKEND le $(date +%F\ %H:%M). À relire avant toute publication."

echo "  · LinkedIn…" >&2
{ echo "# Variante LinkedIn"; echo "$HEADER_NOTE"; echo
  gen "Décline-le en UN post LinkedIn de 150 à 250 mots, ton professionnel : accroche forte en première ligne, corps aéré (phrases courtes, éventuels tirets), une conclusion avec appel à l'action, 3 hashtags pertinents en fin. Pas d'emoji excessif (2 maximum)." 520
} > "$OUT_DIR/01-linkedin.md"

echo "  · X / Twitter…" >&2
{ echo "# Variante X / Twitter"; echo "$HEADER_NOTE"; echo
  gen "Décline-le en UN SEUL tweet de 280 caractères MAXIMUM (compte les caractères), percutant, autoportant, avec au plus 1 hashtag. Donne uniquement le tweet." 180
} > "$OUT_DIR/02-twitter.md"

echo "  · Reel / Short…" >&2
{ echo "# Variante Reel / Short (30-45 s)"; echo "$HEADER_NOTE"; echo
  gen "Décline-le en script de Reel/Short vidéo de 30 à 45 secondes. Format : un HOOK de 3 secondes en ouverture, puis 3 à 5 plans numérotés 'PLAN N (durée s) — [visuel à l'image] : texte dit à voix off', et un appel à l'action final. Ajoute en dernière ligne une suggestion de texte incrusté à l'écran." 520
} > "$OUT_DIR/03-reel-short.md"

echo "  · Carrousel Instagram…" >&2
{ echo "# Variante Carrousel Instagram (5-7 slides)"; echo "$HEADER_NOTE"; echo
  gen "Décline-le en plan de carrousel Instagram de 5 à 7 slides. Format 'Slide N — TITRE COURT : 1 à 2 phrases de contenu'. Slide 1 = accroche visuelle, slides intermédiaires = idées/bénéfices un par slide, dernière slide = appel à l'action + invitation à enregistrer/partager. Ajoute sous le plan une ligne 'Légende :' avec une légende de publication et 5 hashtags." 620
} > "$OUT_DIR/04-carousel-instagram.md"

# ---------------------------------------------------------------------------
# 6. Index récapitulatif
# ---------------------------------------------------------------------------
{
  echo "# Repurpose 1 → 4 — $STAMP"
  echo
  echo "$HEADER_NOTE"
  echo
  echo "## Post source"
  echo '```'
  printf '%s\n' "$SRC"
  echo '```'
  echo
  echo "## Brouillons générés"
  echo "| # | Format | Fichier |"
  echo "|---|--------|---------|"
  echo "| 1 | LinkedIn (150-250 mots) | 01-linkedin.md |"
  echo "| 2 | X / Twitter (≤ 280 car.) | 02-twitter.md |"
  echo "| 3 | Reel / Short (30-45 s) | 03-reel-short.md |"
  echo "| 4 | Carrousel Instagram (5-7 slides) | 04-carousel-instagram.md |"
  echo
  echo "## Prochaine étape"
  echo "Ces fichiers sont des **brouillons**. Rien n'est publié. La mise en ligne"
  echo "se fait manuellement, après validation, par le pilote de publication unique"
  echo "(voir \`~/jarvis/docs/REPURPOSE-1-4.md\`)."
} > "$OUT_DIR/00-INDEX.md"

echo "$OUT_DIR"
