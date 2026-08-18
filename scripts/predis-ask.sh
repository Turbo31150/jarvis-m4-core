#!/usr/bin/env bash
# predis-ask.sh — wrapper JARVIS pour l'API REST Predis.ai (génération contenu social)
# Auth: Authorization: <KEY> | Base: https://brain.predis.ai/predis_api/v1/
# Clé:  ~/.config/predis/api_key (chmod 600)  | Brand: ~/.config/predis/brand_id
#
# Usage:
#   predis-ask.sh create "<texte sujet (min 20 car / 3 mots)>" [media_type] [model_version] [n_posts]
#   predis-ask.sh status <post_id>
#   predis-ask.sh templates
#   predis-ask.sh raw <endpoint> [curl-args...]
#
# media_type: single_image (def) | carousel | video | quote | meme
# model_version: 2 | 4 (def 4)
set -euo pipefail

BASE="https://brain.predis.ai/predis_api/v1"
KEY_FILE="${PREDIS_KEY_FILE:-$HOME/.config/predis/api_key}"
BRAND_FILE="${PREDIS_BRAND_FILE:-$HOME/.config/predis/brand_id}"

[[ -r "$KEY_FILE" ]] || { echo "ERR: clé absente ($KEY_FILE)" >&2; exit 1; }
KEY="$(cat "$KEY_FILE")"
BRAND="${PREDIS_BRAND_ID:-$( [[ -r "$BRAND_FILE" ]] && cat "$BRAND_FILE" || echo '' )}"

auth=(-H "Authorization: $KEY")
cmd="${1:-help}"; shift || true

case "$cmd" in
  create)
    text="${1:?texte sujet requis}"
    media="${2:-single_image}"
    model="${3:-4}"
    n="${4:-1}"
    [[ -n "$BRAND" ]] || { echo "ERR: brand_id manquant. Renseigne $BRAND_FILE (app.predis.ai > Pricing & Account > Brands)" >&2; exit 2; }
    curl -s "${auth[@]}" -X POST "$BASE/create_content/" \
      --data-urlencode "brand_id=$BRAND" \
      --data-urlencode "text=$text" \
      --data-urlencode "media_type=$media" \
      --data-urlencode "model_version=$model" \
      --data-urlencode "n_posts=$n"
    ;;
  status)
    pid="${1:?post_id requis}"
    mt="${2:-carousel}"
    [[ -n "$BRAND" ]] || { echo "ERR: brand_id manquant" >&2; exit 2; }
    curl -s "${auth[@]}" -G "$BASE/get_posts/" \
      --data-urlencode "brand_id=$BRAND" \
      --data-urlencode "media_type=$mt" \
      --data-urlencode "post_id=$pid"
    ;;
  templates)
    [[ -n "$BRAND" ]] || { echo "ERR: brand_id manquant" >&2; exit 2; }
    curl -s "${auth[@]}" -G "$BASE/get_templates/" --data-urlencode "brand_id=$BRAND"
    ;;
  raw)
    ep="${1:?endpoint requis}"; shift || true
    curl -s "${auth[@]}" "$BASE/$ep" "$@"
    ;;
  *)
    grep -E '^#( |$)' "$0" | sed 's/^# \?//'
    ;;
esac
echo
