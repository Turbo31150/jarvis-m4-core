#!/usr/bin/env bash
#
# install-hooks.sh — (re)installe les hooks git du depot planning-app.
#
# Le dossier .git/hooks/ n'est PAS versionne : ce script copie les hooks
# versionnes (scripts/git-hooks/) vers .git/hooks/ et les rend executables.
# A relancer apres un clone frais ou une reinitialisation des hooks.
#
# Hook installe : pre-commit — scanner de secrets (gitleaks + fallback bash)
# qui BLOQUE le commit si un secret est detecte dans les fichiers stages.
#
# Usage : bash bin/install-hooks.sh
#
set -euo pipefail

# Racine du depot (ce script vit dans bin/)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="$REPO_ROOT/scripts/git-hooks"
DST_DIR="$REPO_ROOT/.git/hooks"

if [ ! -d "$REPO_ROOT/.git" ]; then
    echo "Erreur : $REPO_ROOT n'est pas un depot git (.git absent)." >&2
    exit 1
fi
if [ ! -d "$SRC_DIR" ]; then
    echo "Erreur : dossier de hooks versionnes introuvable : $SRC_DIR" >&2
    exit 1
fi

mkdir -p "$DST_DIR"
installed=0
for hook in "$SRC_DIR"/*; do
    [ -f "$hook" ] || continue
    name="$(basename "$hook")"
    cp "$hook" "$DST_DIR/$name"
    chmod +x "$DST_DIR/$name"
    echo "  installe : .git/hooks/$name"
    installed=$((installed + 1))
done

echo "$installed hook(s) installe(s)."

# Info gitleaks (optionnel mais recommande — le hook a un fallback bash sinon)
if command -v gitleaks >/dev/null 2>&1 || [ -x "$HOME/.local/bin/gitleaks" ]; then
    echo "gitleaks detecte : scan authoritatif actif."
else
    cat <<'EOF'
gitleaks NON detecte : le hook utilisera le fallback bash (patterns courants).
Pour installer gitleaks sans sudo :
  mkdir -p ~/.local/bin
  VER=$(curl -fsSL https://api.github.com/repos/gitleaks/gitleaks/releases/latest | grep -m1 tag_name | sed -E 's/.*"v?([^"]+)".*/\1/')
  curl -fsSL "https://github.com/gitleaks/gitleaks/releases/download/v${VER}/gitleaks_${VER}_linux_x64.tar.gz" | tar xz -C ~/.local/bin gitleaks
  chmod +x ~/.local/bin/gitleaks
EOF
fi
