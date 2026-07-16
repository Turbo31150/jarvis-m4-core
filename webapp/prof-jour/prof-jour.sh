#!/usr/bin/env bash
# prof-jour — DEVANCE la journée : contexte du jour (EDT/réunions/absences) + TES supports & mails DÉJÀ créés
# + brouillons prêts, en CASCADE (fetch parallèle), 0-token. PII : reste dans l'app, affichée à toi seule.
# Usage: prof-jour.sh            → brief du jour
#        prof-jour.sh --modeles  → liste les modèles réutilisables
set -uo pipefail
APP="http://127.0.0.1:7777"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOK="$(grep -m1 -oE 'PROF_TOKEN[^=]*=\s*["'"'"']([^"'"'"']+)' ~/jarvis/webapp/prof_routes.py 2>/dev/null | grep -oE '[A-Za-z0-9_-]+$' || true)"
H=(-H "Content-Type: application/json"); [ -n "$TOK" ] && H+=(-H "X-Prof-Token: $TOK")
JOUR="$(date +%A)"; DATE="$(date +%Y-%m-%d)"
OUT="$HERE/_jour"; mkdir -p "$OUT"

if [ "${1:-}" = "--modeles" ]; then
  echo "📄 Modèles réutilisables ($HERE/modeles) :"; ls "$HERE/modeles" | sed 's/^/  • /'; exit 0
fi

q(){ curl -s -m4 "${H[@]}" "$APP$1" 2>/dev/null; }

# ── CASCADE : on lance les fetchs du contexte EN PARALLÈLE ──
echo "🌊 prof-jour — cascade contexte ($JOUR $DATE)…"
q "/api/prof/edt"            > "$OUT/edt.json"       &
q "/api/appel/$DATE"         > "$OUT/absences.json"  &
q "/api/reunions"            > "$OUT/reunions.json"  &
q "/api/mail/log"            > "$OUT/mails.json"     &
q "/api/docs"                > "$OUT/docs.json"      &
q "/api/prof/ressources"     > "$OUT/ressources.json" &
wait

jqf(){ command -v jq >/dev/null 2>&1 && jq -r "$1" "$2" 2>/dev/null || echo "(jq absent — voir $2)"; }

echo; echo "🗓️  EDT du jour ($JOUR) :"
jq -r --arg j "$JOUR" '.[$j] // "(rien programmé)"' "$OUT/edt.json" 2>/dev/null | sed 's/^/  /'
echo; echo "🚸 Absents ($DATE) — brouillon mail-absence prêt par élève :"
jq -r '[.[]?|select(.present==0)] | if length==0 then "  (aucun absent 👍)" else (.[]|"  • \(.prenom) \(.nom) (id \(.eleve_id))") end' "$OUT/absences.json" 2>/dev/null
echo; echo "👥 Réunions à venir — ordre-du-jour/CR réutilisables :"
jqf '.[]? | "  • \(.date // "?")  \(.titre // .type // "réunion")"' "$OUT/reunions.json" | head -10
echo; echo "✉️  Mails DÉJÀ générés (réutiliser le style/ton) :"
jqf '.[]? | "  • \(.created_at // "?")  \(.sujet // .objet // "mail")  [\(.statut // "")]"' "$OUT/mails.json" | head -10
echo; echo "📚 Supports/docs DÉJÀ créés (Drive/app) à réemployer :"
jqf '.[]? | "  • \(.nom // .titre // .name // .)"' "$OUT/docs.json" | head -12

cat <<EOF

⚙️  DEVANCER (0-token, tout est déjà câblé) :
  • Mail parent perso   : curl -s -X POST $APP/api/mail-parent/draft -d '{"motif":"...","eleve_id":<id>}'
  • Modèles neutres     : bash $HERE/prof-jour.sh --modeles   (mail-*, autorisation-sortie, ordre-du-jour, convocation, avis-absence)
  • Réutilise l'existant: tes mails/docs ci-dessus = base ; je génère au même ton via /api/mail-parent/draft (cache ai_local).
EOF
