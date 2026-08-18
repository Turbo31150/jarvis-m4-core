#!/usr/bin/env bash
# git-guard.sh — Protection anti-fuite de secrets pour les repos JARVIS (bibliothèque/domino/backup)
# Usage:
#   git-guard.sh check              # scanne l'index staged (utilisé par le hook pre-commit) → exit 1 si secret
#   git-guard.sh check-tree <dir>   # scanne tout un arbre de travail
#   git-guard.sh install <repo>     # installe le hook pre-commit + pre-push + .gitignore durci dans <repo>
# Bloque : secrets.db, *.pem, *.key, id_rsa/id_ed25519, .env, dumps pg_*.sql*, et patterns de clés API.
set -uo pipefail

# Fichiers/chemins interdits (regex sur le path)
BLOCK_PATHS='(^|/)(secrets\.db|.*\.pem|.*\.key|id_(rsa|ed25519)|\.env(\..*)?|pg_.*\.sql(\.gz)?|.*_pg_dump.*\.sql.*|.*credentials.*\.(db|sqlite|json))$'
# Patterns de secrets dans le contenu (clés API live)
BLOCK_CONTENT='(mrr_live_[A-Za-z0-9]{10}|sk-[A-Za-z0-9]{20}|ghp_[A-Za-z0-9]{20}|gho_[A-Za-z0-9]{20}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30}|glpat-[0-9A-Za-z_-]{20}|nfp_[A-Za-z0-9]{20})'

scan_paths() { # $1 = liste de fichiers (stdin) → imprime les violations
  grep -E "$BLOCK_PATHS" || true
}

cmd_check() { # scanne l'index git staged
  local viol=0
  local staged; staged=$(git diff --cached --name-only 2>/dev/null)
  [ -z "$staged" ] && exit 0
  # 1) chemins interdits
  local bad_paths; bad_paths=$(echo "$staged" | grep -E "$BLOCK_PATHS" || true)
  if [ -n "$bad_paths" ]; then echo "🛑 git-guard: fichiers interdits (secrets):"; echo "$bad_paths" | sed 's/^/   /'; viol=1; fi
  # 2) contenu interdit (fichiers texte staged)
  while IFS= read -r f; do
    [ -f "$f" ] || continue
    if LC_ALL=C grep -aEl "$BLOCK_CONTENT" "$f" >/dev/null 2>&1; then
      echo "🛑 git-guard: secret en clair dans $f"; viol=1
    fi
  done <<< "$staged"
  [ "$viol" -eq 1 ] && { echo "→ Retire ces éléments (git rm --cached / .gitignore) ou chiffre-les avant de committer."; exit 1; }
  exit 0
}

cmd_check_tree() {
  local d="${1:-.}"
  echo "=== git-guard scan-tree $d ==="
  find "$d" -type f 2>/dev/null | grep -E "$BLOCK_PATHS" | sed 's/^/  PATH  /' || true
  grep -rElaI "$BLOCK_CONTENT" "$d" 2>/dev/null | sed 's/^/  KEY   /' || true
  echo "=== fin scan ==="
}

cmd_install() {
  local repo="${1:?repo requis}"
  [ -d "$repo/.git" ] || { echo "❌ $repo n'est pas un repo git"; exit 1; }
  local self; self=$(readlink -f "$0")
  # pre-commit
  cat > "$repo/.git/hooks/pre-commit" <<HOOK
#!/usr/bin/env bash
exec "$self" check
HOOK
  chmod +x "$repo/.git/hooks/pre-commit"
  # pre-push (double filet)
  cat > "$repo/.git/hooks/pre-push" <<HOOK
#!/usr/bin/env bash
"$self" check-tree "\$(git rev-parse --show-toplevel)" | grep -qE 'PATH|KEY' && { echo "🛑 git-guard pre-push: secrets présents, push bloqué."; exit 1; }
exit 0
HOOK
  chmod +x "$repo/.git/hooks/pre-push"
  # .gitignore durci (append si absent)
  local gi="$repo/.gitignore"; touch "$gi"
  for p in 'secrets.db' '*.pem' '*.key' 'id_rsa' 'id_ed25519' '.env' '.env.*' 'pg_*.sql' 'pg_*.sql.gz' '*_pg_dump*.sql*' '*credentials*.db'; do
    grep -qxF "$p" "$gi" 2>/dev/null || echo "$p" >> "$gi"
  done
  echo "✅ git-guard installé sur $repo (pre-commit + pre-push + .gitignore durci)"
}

case "${1:-check}" in
  check)       cmd_check ;;
  check-tree)  cmd_check_tree "${2:-.}" ;;
  install)     cmd_install "${2:-}" ;;
  *) echo "usage: git-guard.sh {check|check-tree <dir>|install <repo>}"; exit 2 ;;
esac
