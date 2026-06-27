#!/bin/bash
# gemini-ask.sh — Thin wrapper → gemini-smart.sh (rétrocompat MCP + scripts)
# Usage identique à l'original : gemini-ask.sh [--flash|--model ID|--no-fallback] "prompt"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/gemini-smart.sh" "$@"
