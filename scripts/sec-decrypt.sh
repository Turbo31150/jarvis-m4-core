#!/usr/bin/env bash
# sec-decrypt.sh — déchiffre un secret du coffre au moment de l'usage.
# Usage : source sec-decrypt.sh <nom>   → exporte les variables dans le shell courant
#         sec-decrypt.sh <nom>          → affiche en clair (à éviter ; debug seulement)
# Ex.   : source ~/jarvis/scripts/sec-decrypt.sh secrets   # charge secrets.enc.env
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
export SOPS_AGE_KEY_FILE="${SOPS_AGE_KEY_FILE:-$HOME/.config/sops/age/keys.txt}"
VAULT="$HOME/jarvis/secrets-vault"
name="${1:?usage: sec-decrypt.sh <nom> (ex: secrets, openclaw, github-social)}"
file="$VAULT/${name}.enc.env"
[ -f "$file" ] || { echo "introuvable: $file" >&2; return 1 2>/dev/null || exit 1; }
if (return 0 2>/dev/null); then
  # sourcé → exporte les variables sans jamais écrire de clair sur disque
  set -a; eval "$(sops -d --input-type dotenv --output-type dotenv "$file")"; set +a
  echo "secrets '$name' chargés en mémoire (non écrits sur disque)." >&2
else
  sops -d --input-type dotenv --output-type dotenv "$file"
fi
