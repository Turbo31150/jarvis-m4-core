#!/usr/bin/env bash
# SERIE: a11y-check — accessibilité de base par page (lecture seule) : alt images, lang, labels de formulaire, liens vides, boutons sans texte
set -uo pipefail
SITE="${1:?usage: lib.sh run a11y-check <dossier_site>}"
[ -d "$SITE" ] || { echo "⛔ dossier introuvable: $SITE"; exit 1; }

echo "== Accessibilité (a11y) — $SITE =="
shopt -s nullglob
pages=("$SITE"/*.html)
[ ${#pages[@]} -eq 0 ] && { echo "  (aucune page .html)"; exit 0; }

for f in "${pages[@]}"; do
  b=$(basename "$f"); h=$(tr '[:upper:]' '[:lower:]' < "$f" | tr '\n' ' ')
  msgs=()
  grep -q '<html[^>]*lang=' <<<"$h" || msgs+=("attribut lang manquant")
  noalt=$(grep -o '<img[^>]*>' <<<"$h" | grep -vc 'alt=' || true)
  [ "${noalt:-0}" -gt 0 ] && msgs+=("$noalt image(s) sans alt")
  inputs=$(grep -o '<input' <<<"$h" | wc -l)
  labels=$(grep -o '<label' <<<"$h" | wc -l)
  { [ "$inputs" -gt 0 ] && [ "$labels" -lt "$inputs" ]; } && msgs+=("$inputs input / $labels label (libellés possibles manquants)")
  emptylinks=$(grep -oE '<a [^>]*href="#?"[^>]*>\s*</a>' <<<"$h" | wc -l)
  [ "$emptylinks" -gt 0 ] && msgs+=("$emptylinks lien(s) vide(s)")
  if [ ${#msgs[@]} -eq 0 ]; then echo "  ✓ $b"; else echo "  ⚠ $b : ${msgs[*]}"; fi
done
