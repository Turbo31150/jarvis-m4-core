#!/usr/bin/env bash
# security-check.sh — audit sécurité pre-push : gitleaks (repo entier) + trivy.
set -Eeuo pipefail

GITLEAKS="$(git rev-parse --show-toplevel)/bin/gitleaks"
[ -x "$GITLEAKS" ] || GITLEAKS="$(command -v gitleaks || true)"
if [ -n "$GITLEAKS" ] && [ -x "$GITLEAKS" ]; then
  "$GITLEAKS" detect --source . --redact --no-banner
fi

if command -v trivy >/dev/null 2>&1; then
  trivy fs --exit-code 1 --severity HIGH,CRITICAL .
fi
exit 0
