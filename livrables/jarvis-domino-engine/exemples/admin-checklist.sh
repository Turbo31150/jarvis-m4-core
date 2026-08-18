#!/usr/bin/env bash
# SERIE: admin-checklist — checklist 0-token des pièces à fournir pour une démarche donnée
set -uo pipefail
source "$HOME/labo/bibliotheque/outils/admin-lib.sh"
SUJET="${1:?usage: lib.sh run admin-checklist \"<consigne>\" [sortie]}"
OUT="${2:-$ADMIN_OUT/checklist-$(echo "$SUJET" | tr -cd 'A-Za-z0-9_' | cut -c1-40).md}"
PROMPT=$(cat <<'PH'
Donne la checklist complète et à jour des pièces justificatives à fournir pour la démarche administrative suivante: @@SUBJTOKEN@@. Présente un tableau: pièce | obligatoire ? | où l'obtenir | format/validité. Ajoute délais et pièges courants. Français.
PH
)
PROMPT="${PROMPT//@@SUBJTOKEN@@/$SUJET}"
RES=$(ai_cascade "$PROMPT" speed)
[ -n "${RES:-}" ] || { echo "⛔ aucune réponse (cluster+OL1 down)"; exit 2; }
{ echo "# Checklist: $SUJET"; echo; echo "$RES"; } > "$OUT"; echo "✅ écrit: $OUT"
