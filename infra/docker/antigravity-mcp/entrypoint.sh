#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8902}"
ANTIGRAV_SCRIPT="${ANTIGRAV_SCRIPT:-/usr/local/bin/antigravity-ask.sh}"
LOG_PREFIX="[antigravity-mcp]"

echo "${LOG_PREFIX} Starting supergateway bridge (PID $$)"
echo "${LOG_PREFIX} Port: ${PORT}"
echo "${LOG_PREFIX} Stdio child: bash ${ANTIGRAV_SCRIPT} --model claude-sonnet --max 1500"

if [ ! -x "${ANTIGRAV_SCRIPT}" ]; then
    echo "${LOG_PREFIX} FATAL: antigravity-ask.sh introuvable ou non-exécutable à ${ANTIGRAV_SCRIPT}" >&2
    exit 78  # EX_CONFIG
fi

# Pré-flight : vérifier que bash + curl répondent (sinon image cassée)
command -v bash >/dev/null || { echo "${LOG_PREFIX} FATAL: bash manquant" >&2; exit 78; }
command -v curl >/dev/null || { echo "${LOG_PREFIX} FATAL: curl manquant" >&2; exit 78; }

trap 'echo "${LOG_PREFIX} SIGTERM reçu, shutdown propre"; exit 0' SIGTERM SIGINT

exec npx -y supergateway \
    --stdio "bash ${ANTIGRAV_SCRIPT} --model claude-sonnet --max 1500" \
    --port "${PORT}" \
    --healthEndpoint /health
