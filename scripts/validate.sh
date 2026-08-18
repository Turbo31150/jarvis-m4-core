#!/usr/bin/env bash
# validate.sh — lint/typecheck/tests selon la stack détectée à la racine.
# jarvis-core n'a pas de manifeste racine aujourd'hui : no-op volontaire,
# le script devient actif dès qu'un package.json/pyproject.toml apparaît.
set -Eeuo pipefail

if [ -f package.json ]; then
  npm run lint --if-present
  npm run typecheck --if-present
  npm test --if-present
fi

if [ -f pyproject.toml ] || [ -f pytest.ini ]; then
  python3 -m pytest -q
fi

if [ -f go.mod ]; then
  go test ./...
fi
exit 0
