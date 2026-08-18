#!/usr/bin/env bash
# Lance le serveur MCP Notion officiel avec le token déchiffré depuis le coffre sops.
set -euo pipefail

VAULT="$HOME/jarvis/secrets-vault/notion.enc.env"
export SOPS_AGE_KEY_FILE="$HOME/.config/sops/age/keys.txt"

NOTION_TOKEN="$("$HOME/.local/bin/sops" -d "$VAULT" | awk -F= '/^NOTION_TOKEN=/{print $2}')"
[ -n "$NOTION_TOKEN" ] || { echo "ERREUR: NOTION_TOKEN introuvable dans le coffre" >&2; exit 1; }

export NOTION_TOKEN
exec npx -y @notionhq/notion-mcp-server
