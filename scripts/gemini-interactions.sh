#!/usr/bin/env bash
# gemini-interactions.sh — Wrapper d'exécution pour JARVIS Gemini Interactions API
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="/home/pamerys/Workspaces/jarvis-linux:${PYTHONPATH:-}"
exec python3 "$SCRIPT_DIR/gemini-interactions.py" "$@"
