#!/usr/bin/env bash
# Générateur cascade 0-token : remplit un modèle de communication via l'IA locale OL1.
# Usage :
#   ./generer.sh                         → liste les modèles
#   ./generer.sh mail-difficulte "Léo, oublie souvent son matériel, propose un RDV"
#   ./generer.sh mot-sortie "musée du Louvre, 12 mai, car, pique-nique"
# Sortie : brouillon prêt à relire, affiché + sauvegardé dans brouillons/
set -uo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
OL1="http://127.0.0.1:11434/api/generate"
MODEL="${MODEL:-qwen2.5:7b}"
mkdir -p "$DIR/brouillons"

# Retrouve un modèle par nom (sans extension), quel que soit le sous-dossier
type="${1:-}"
if [ -z "$type" ]; then
  echo "📋 Modèles disponibles :"
  find "$DIR" -name '*.md' ! -name 'README.md' | sed "s|$DIR/||; s|\.md$||" | sort | sed 's/^/  • /'
  echo; echo "Usage : ./generer.sh <type> \"faits datés + issue (RDV/aide)\""
  exit 0
fi
tpl="$(find "$DIR" -name "$(basename "$type").md" | head -1)"
[ -f "$tpl" ] || { echo "❌ modèle inconnu : $type (lance sans argument pour la liste)"; exit 1; }
faits="${*:2}"; faits="${faits:-à compléter}"

echo "⚙️  Cascade OL1 ($MODEL) — modèle : $(basename "$tpl" .md)…"
tmpl_content="$(cat "$tpl")"
prompt=$(cat <<PROMPT
Tu es professeure des écoles en France. À partir du MODÈLE ci-dessous, rédige un texte
FINAL prêt à envoyer, en français, vouvoiement, ton professionnel et chaleureux.
Règles : factuel, jamais de jugement sur l'enfant, ne mentionne AUCUN autre élève,
termine par une solution ou un RDV, garde la signature. Remplace les {{…}} par les
informations fournies ; pour ce qui manque, laisse un {{…}} clair à compléter.
Réponds UNIQUEMENT par le texte final (objet + corps), sans commentaire.

FAITS À INTÉGRER : $faits

MODÈLE :
$tmpl_content
PROMPT
)

out="$(curl -s -m120 "$OL1" -d "$(jq -n --arg m "$MODEL" --arg p "$prompt" '{model:$m,prompt:$p,stream:false}')" 2>/dev/null | jq -r '.response' 2>/dev/null)"
if [ -z "$out" ] || [ "$out" = "null" ]; then
  echo "⚠️  OL1 muet — fallback : modèle brut à remplir à la main :"; echo; cat "$tpl"; exit 0
fi

f="$DIR/brouillons/$(basename "$type")-$(date +%Y%m%d-%H%M%S).md"
printf '%s\n' "$out" | tee "$f"
echo; echo "💾 Brouillon : ${f#$DIR/}  — À RELIRE avant envoi (vérifie faits, dates, RGPD)."
