#!/usr/bin/env bash
# openclaw-redeploy.sh — Redéploiement idempotent de la stack OpenClaw JARVIS
# Cible : machine fraîche (re-image M3) ou reconstruction reproductible.
# Provider par défaut : LM Studio M1 (OpenAI-compatible, 0€ API).
#
# SÉCURITÉ : dry-run par défaut. Affiche les commandes sans rien exécuter.
#            Ajoute --apply pour exécuter réellement.
#            onboard n'est lancé QUE si aucune config n'existe (garde idempotente),
#            sauf --force-onboard explicite.
#
# Flags vérifiés contre `openclaw onboard --help` / `openclaw agents add --help`
# sur OpenClaw 2026.3.11 (29dc654).
set -euo pipefail

# ---- Config (adapter ici) -------------------------------------------------
LMS_BASE_URL="${LMS_BASE_URL:-http://127.0.0.1:1234/v1}"   # LM Studio M1
LMS_MODEL="${LMS_MODEL:-qwen3.5-9b}"
GATEWAY_PORT="${GATEWAY_PORT:-18789}"
GATEWAY_BIND="${GATEWAY_BIND:-loopback}"                       # loopback|tailnet|lan|auto|custom
OC_HOME="${OC_HOME:-$HOME/.openclaw}"

# Manifeste des agents à (re)créer : "nom:modèle:binding"
# binding vide = pas de routage canal. Adapter à ta liste réelle.
AGENTS=(
  "trading:${LMS_MODEL}:"
  "mail:${LMS_MODEL}:"
  "linkedin:${LMS_MODEL}:"
  "sysops:${LMS_MODEL}:"
)

# ---- Args -----------------------------------------------------------------
APPLY=0
FORCE_ONBOARD=0
for a in "$@"; do
  case "$a" in
    --apply) APPLY=1 ;;
    --force-onboard) FORCE_ONBOARD=1 ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Flag inconnu: $a" >&2; exit 2 ;;
  esac
done

run() {
  if [ "$APPLY" -eq 1 ]; then
    echo "+ $*"; "$@"
  else
    echo "[dry-run] $*"
  fi
}

# ---- Pré-vol --------------------------------------------------------------
command -v openclaw >/dev/null || { echo "❌ openclaw absent du PATH"; exit 1; }
echo "ℹ️  $(openclaw --version 2>/dev/null | head -1)"
echo "ℹ️  Provider: LM Studio @ ${LMS_BASE_URL} (modèle ${LMS_MODEL})"
echo "ℹ️  Mode: $([ "$APPLY" -eq 1 ] && echo APPLY || echo DRY-RUN)"
echo

# Vérifie joignabilité LM Studio avant de configurer dessus
if ! curl -sf -m 4 "${LMS_BASE_URL%/v1}/v1/models" >/dev/null 2>&1; then
  echo "⚠️  LM Studio injoignable sur ${LMS_BASE_URL} — onboard configurera quand même, mais les agents échoueront tant que le backend est down."
fi

# ---- Onboard (idempotent) -------------------------------------------------
if [ -f "$OC_HOME/config.json" ] || [ -d "$OC_HOME/agents" ]; then
  if [ "$FORCE_ONBOARD" -eq 1 ]; then
    echo "⚠️  Config existante détectée + --force-onboard → onboard avec --reset config (creds/sessions préservés)."
    run openclaw onboard --non-interactive --accept-risk \
      --mode local \
      --flow quickstart \
      --auth-choice custom-api-key \
      --custom-provider-id lmstudio-m1 \
      --custom-base-url "$LMS_BASE_URL" \
      --custom-compatibility openai \
      --custom-model-id "$LMS_MODEL" \
      --custom-api-key "lm-studio" \
      --secret-input-mode plaintext \
      --gateway-port "$GATEWAY_PORT" \
      --gateway-bind "$GATEWAY_BIND" \
      --install-daemon --daemon-runtime node \
      --skip-skills --skip-search \
      --reset --reset-scope config \
      --json
  else
    echo "✅ Config OpenClaw déjà présente ($OC_HOME) → onboard SAUTÉ (idempotent). Utilise --force-onboard pour forcer."
  fi
else
  echo "🆕 Aucune config → onboard initial."
  run openclaw onboard --non-interactive --accept-risk \
    --mode local \
    --flow quickstart \
    --auth-choice custom-api-key \
    --custom-provider-id lmstudio-m1 \
    --custom-base-url "$LMS_BASE_URL" \
    --custom-compatibility openai \
    --custom-model-id "$LMS_MODEL" \
    --custom-api-key "lm-studio" \
    --secret-input-mode plaintext \
    --gateway-port "$GATEWAY_PORT" \
    --gateway-bind "$GATEWAY_BIND" \
    --install-daemon --daemon-runtime node \
    --skip-skills --skip-search \
    --json
fi
echo

# ---- Agents (idempotent par workspace) ------------------------------------
for entry in "${AGENTS[@]}"; do
  IFS=':' read -r name model bind <<< "$entry"
  ws="$OC_HOME/workspace-$name"
  if [ -d "$ws" ]; then
    echo "✅ agent '$name' déjà présent ($ws) → sauté."
    continue
  fi
  bind_flag=()
  [ -n "$bind" ] && bind_flag=(--bind "$bind")
  run openclaw agents add "$name" \
    --workspace "$ws" \
    --model "${model:-$LMS_MODEL}" \
    "${bind_flag[@]}" \
    --non-interactive --json
done

echo
echo "✔️  Terminé ($([ "$APPLY" -eq 1 ] && echo APPLIQUÉ || echo DRY-RUN)). Vérifie: openclaw agents list"
