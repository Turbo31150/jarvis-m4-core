#!/usr/bin/env bash
# Route CLI : génère slides locales → upload Mirra → crée post draft IG
# Contourne quota AI Mirra. Pipeline complet en 1 commande.
#
# Usage:
#   ./route.sh                    # full pipeline (gen + upload + post draft)
#   ./route.sh --gen-only         # juste régénérer les images
#   ./route.sh --publish <postId> # publish maintenant un draft existant
#
set -euo pipefail

ROUTE_DIR="$(cd "$(dirname "$0")" && pwd)"
SLIDES_DIR="/tmp/mirra-slides"
ACCOUNT_IG="a8bf4841-a64b-4d75-b752-0b992f0678b0"   # franckonfray Instagram

cmd="${1:-full}"

case "$cmd" in
  --gen-only)
    python3 "$ROUTE_DIR/gen_slides.py"
    echo "→ Slides dans $SLIDES_DIR/"
    ;;
  --publish)
    POST_ID="${2:?usage: route.sh --publish <postId>}"
    echo "TODO: exposer post_publish_now via CLI Mirra (utiliser MCP via claude)"
    echo "Pour l'instant : ouvre https://www.mirra.my/fr/posts/$POST_ID"
    ;;
  full|*)
    echo "[1/3] Génération slides…"
    python3 "$ROUTE_DIR/gen_slides.py"
    echo ""
    echo "[2/3] Upload + post-create : utiliser MCP Mirra via Claude Code"
    echo "      (les outils MCP ne sont pas exposés en CLI direct)"
    echo ""
    echo "[3/3] Workflow :"
    echo "  - Slides prêtes : $SLIDES_DIR/slide_{1..6}.jpg"
    echo "  - Compte IG cible : $ACCOUNT_IG"
    echo "  - Dashboard : https://www.mirra.my/fr/social-accounts/$ACCOUNT_IG"
    ;;
esac
