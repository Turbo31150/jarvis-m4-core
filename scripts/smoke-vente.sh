#!/usr/bin/env bash
# smoke-vente.sh — Smoke-test LECTURE SEULE des URL d'encaissement (PayPal/Netlify + Gumroad + systeme.io)
# But : vérifier AVANT / APRÈS le redeploy Netlify que les URL de retour paiement répondent.
# 0 secret, idempotent, aucune écriture en ligne, exit 0 toujours.
# Préparé par NETLIFY-PREP (tâche #14). Voir page Notion « Prêt-à-réparer — Encaissement Netlify/PayPal ».
set -uo pipefail

# ── Cible principale : site Netlify qui héberge la fonction IPN + pages /merci /cgv ──
BASE="${BASE:-https://jarvis-delmas.netlify.app}"

# URL clés (toutes référencées par les 56 formulaires PayPal de jarvis-products.html)
declare -a URLS=(
  "$BASE/|Accueil boutique|200"
  "$BASE/.netlify/functions/paypal-ipn|Fonction Netlify IPN PayPal (notify_url)|200,405,400"
  "$BASE/merci|Page retour succès (return)|200"
  "$BASE/cgv|Page CGV|200"
  "$BASE/mentions-legales|Mentions légales|200"
  "$BASE/confidentialite|Confidentialité RGPD|200"
)

# ── Gumroad : profil + fiches produit ──
# IMPORTANT : toujours tester en VENDEUR-SCOPÉ (franckdelmas.gumroad.com/l/<slug>).
# Le namespace gumroad.com/l/<slug> est GLOBAL et peut renvoyer un faux 200 pour
# un produit d'un autre vendeur → ne jamais l'utiliser pour ce contrôle.
GUMROAD_BASE="${GUMROAD_BASE:-https://franckdelmas.gumroad.com}"
# Slugs à vérifier (mettre à jour depuis le diag ; ceux du catalogue par défaut).
declare -a GUMROAD_SLUGS=(
  "ia-fondamentaux-2026"
  "prompt-engineering"
  "vibe-coding"
  "claude-code-mastery-m1"
  "claude-code-pro"
  "jarvis-os-cluster"
  "jarvis-mcp-toolkit"
)
# Slugs MORTS confirmés 404 (vérifiés vendeur-scopé le 2026-08-14, 15h30) : 4 exactement.
declare -a GUMROAD_SLUGS_404=(
  "pack-complet-jarvis-os"
  "jarvis-os-cluster-complet"
  "agents-autonomes-mcp"
  "ia-healthcare"
)

# ── systeme.io (tunnel Franck Delmas) — override via SYSTEMEIO_URL=... ──
SYSTEMEIO_URL="${SYSTEMEIO_URL:-}"

TIMEOUT="${TIMEOUT:-15}"
UA="smoke-vente/1.0 (+read-only)"
pass=0; fail=0; skip=0

http_code() {
  curl -s -o /dev/null -w '%{http_code}' -A "$UA" \
    --max-time "$TIMEOUT" -L "$1" 2>/dev/null || echo "000"
}

check() {
  local url="$1" label="$2" ok_codes="$3"
  local code; code="$(http_code "$url")"
  if [[ ",$ok_codes," == *",$code,"* ]]; then
    printf '  \033[32mPASS\033[0m  %-4s  %-42s  %s\n' "$code" "$label" "$url"
    pass=$((pass+1))
  else
    printf '  \033[31mFAIL\033[0m  %-4s  %-42s  %s\n' "$code" "$label" "$url"
    fail=$((fail+1))
  fi
}

echo "=================================================================="
echo " SMOKE-TEST VENTE — $(date '+%Y-%m-%d %H:%M:%S')"
echo " Base Netlify : $BASE"
echo "=================================================================="

echo; echo "[1] Netlify / PayPal (return · notify_url · pages légales)"
for row in "${URLS[@]}"; do
  IFS='|' read -r url label codes <<< "$row"
  check "$url" "$label" "$codes"
done

echo; echo "[2] Gumroad (profil + fiches produit)"
check "$GUMROAD_BASE/" "Profil Gumroad" "200"
for slug in "${GUMROAD_SLUGS[@]}"; do
  check "$GUMROAD_BASE/l/$slug" "produit: $slug" "200"
done
echo "  -- 4 slugs MORTS confirmés (attendu 404, vendeur-scopé) --"
for slug in "${GUMROAD_SLUGS_404[@]}"; do
  check "$GUMROAD_BASE/l/$slug" "mort(404 attendu): $slug" "404"
done

echo; echo "[3] systeme.io"
if [[ -n "$SYSTEMEIO_URL" ]]; then
  check "$SYSTEMEIO_URL" "tunnel systeme.io" "200"
else
  echo "  SKIP  ----  systeme.io (définir SYSTEMEIO_URL=... pour tester)"
  skip=$((skip+1))
fi

echo
echo "------------------------------------------------------------------"
echo " RÉSULTAT : PASS=$pass  FAIL=$fail  SKIP=$skip"
if [[ $fail -gt 0 ]]; then
  echo " => Des URL sont en échec. Si paypal-ipn / merci / cgv en 404 :"
  echo "    le site Netlify jarvis-delmas n'est pas reconnecté au repo."
  echo "    Suivre la procédure dashboard (page Notion Prêt-à-réparer)."
else
  echo " => Toutes les URL testées répondent. Encaissement opérationnel."
fi
echo "------------------------------------------------------------------"
exit 0
