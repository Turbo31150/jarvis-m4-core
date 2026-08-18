#!/usr/bin/env bash
# checkpoint.sh — Sauvegarde sécurisée d'une app : backup SQLite local + commit/push
# GitHub du CODE uniquement, avec garde-fou qui REFUSE de pousser PII/secrets/binaires.
#
# Usage : checkpoint.sh [APP_DIR] [-m "message commit"] [--dry-run] [--no-push]
# Défaut APP_DIR = ~/jarvis/webapp
#
# Principe RGPD : les bases (*.db) contiennent des données élèves → JAMAIS sur GitHub.
# Elles sont sauvegardées EN LOCAL (backups/) ; seul le code part sur le dépôt distant.
set -euo pipefail

APP_DIR="${1:-$HOME/jarvis/webapp}"; [[ "${APP_DIR:0:1}" == "-" ]] && APP_DIR="$HOME/jarvis/webapp"
MSG=""; DRY=0; PUSH=1
while [[ $# -gt 0 ]]; do case "$1" in
  -m) MSG="$2"; shift 2;;
  --dry-run) DRY=1; shift;;
  --no-push) PUSH=0; shift;;
  *) shift;;
esac; done

cd "$APP_DIR" || { echo "❌ APP_DIR introuvable: $APP_DIR"; exit 1; }
TS="$(date +%Y%m%d-%H%M)"
echo "📁 App : $APP_DIR"

# 1) Backup SQLite LOCAL (méthode .backup = cohérente même base ouverte)
mkdir -p backups
shopt -s nullglob
for db in *.db; do
  sqlite3 "$db" ".backup 'backups/${db%.db}-$TS.db'" && \
    echo "💾 backups/${db%.db}-$TS.db ($(du -h "backups/${db%.db}-$TS.db" | cut -f1))"
done
shopt -u nullglob

# 2) Garantir un .gitignore protecteur (créé s'il manque)
if [[ ! -f .gitignore ]] || ! grep -q "checkpoint-securise-app" .gitignore; then
  cat >> .gitignore <<'EOF'

# === checkpoint-securise-app : exclusions de sécurité ===
*.db
backups/
*.env
.env
*.token
.*_token
*secret*
*.key
*.pem
certs/
__pycache__/
*.pyc
.ruff_cache/
EOF
  echo "🛡️  .gitignore mis à jour (PII/secrets exclus)"
fi

# 3) Stager UNIQUEMENT le code + docs (jamais les binaires lourds ni data)
# nullglob : un motif sans correspondance disparaît au lieu de faire échouer `git add`
shopt -s nullglob
FILES=(.gitignore *.py *.html *.md *.json *.js *.css *.txt)
[[ -d scripts ]] && FILES+=(scripts)   # inclut les .sh/.py des sous-dossiers de code
shopt -u nullglob
[[ ${#FILES[@]} -gt 0 ]] && git add -- "${FILES[@]}"

# 4) GARDE-FOU : refuser tout secret / PII / binaire dans l'index
LEAK="$(git diff --cached --name-only | grep -iE '\.db$|\.env$|\.token|secret|\.pem$|\.key$|certs/|/logiciels/|\.(exe|appimage|jar|bin)$' || true)"
if [[ -n "$LEAK" ]]; then
  echo "🔴 STOP — fichiers sensibles/binaires détectés dans l'index :"; echo "$LEAK" | sed 's/^/   /'
  git reset -q -- $LEAK
  echo "→ retirés de l'index. Vérifie ton .gitignore avant de relancer."; exit 2
fi

STAGED="$(git diff --cached --name-only | wc -l)"
echo "✅ $STAGED fichier(s) code/docs staged, 0 secret/PII (garde-fou OK)"
git diff --cached --name-only | sed 's/^/   + /'

if [[ "$DRY" == "1" ]]; then echo "🧪 --dry-run : aucun commit/push."; exit 0; fi
if [[ "$STAGED" == "0" ]]; then echo "ℹ️  Rien à committer (backup local fait)."; exit 0; fi

# 5) Commit (avec trailer co-auteur) + push branche courante
BR="$(git branch --show-current)"
[[ -z "$MSG" ]] && MSG="checkpoint($(basename "$APP_DIR")): sauvegarde $TS"
git commit -q -m "$MSG" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
echo "📌 commit sur $BR : $(git rev-parse --short HEAD)"
if [[ "$PUSH" == "1" ]]; then
  git push origin "$BR" && echo "🚀 poussé sur origin/$BR"
else
  echo "⏸️  --no-push : commit local seulement."
fi
