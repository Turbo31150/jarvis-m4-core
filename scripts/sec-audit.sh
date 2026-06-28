#!/usr/bin/env bash
# ============================================================================
# sec-audit.sh — Red-team reproductible (lecture seule, valeurs MASQUÉES)
# Vérifie l'exposition réelle des secrets/données sur la machine.
# Objectif : DOIT échouer à lire des secrets une fois le durcissement appliqué.
# Usage : bash sec-audit.sh   (aucune modif, aucun secret affiché en clair)
# ============================================================================
set -uo pipefail
RED=$'\e[31m'; GRN=$'\e[32m'; YEL=$'\e[33m'; RST=$'\e[0m'
ko(){ echo "${RED}✗ $*${RST}"; }
ok(){ echo "${GRN}✓ $*${RST}"; }
wn(){ echo "${YEL}! $*${RST}"; }
hr(){ printf '%s\n' "──────────────────────────────────────────────"; }

echo "=== SEC-AUDIT $(date '+%F %T') sur $(hostname) ==="

hr; echo "[1] Chiffrement disque (LUKS)"
if lsblk -o FSTYPE 2>/dev/null | grep -qi crypt; then ok "chiffrement disque présent"; else ko "AUCUN chiffrement disque (disque volé = lisible)"; fi

hr; echo "[2] Bases SQLite en clair (échantillon, schémas seulement)"
clear_db=0
while IFS= read -r db; do
  if file -b "$db" 2>/dev/null | grep -qi "SQLite 3"; then clear_db=$((clear_db+1)); fi
done < <(find "$HOME" /opt -maxdepth 5 \( -name '*.db' -o -name '*.sqlite*' \) 2>/dev/null | grep -v node_modules)
if [ "$clear_db" -gt 0 ]; then ko "$clear_db base(s) SQLite EN CLAIR (lisibles sans clé)"; else ok "aucune base SQLite en clair"; fi

hr; echo "[3] Clés SSH sans passphrase"
nopass=0
for k in "$HOME"/.ssh/id_*; do
  [ -f "$k" ] || continue; case "$k" in *.pub) continue;; esac
  if ssh-keygen -y -P "" -f "$k" >/dev/null 2>&1; then nopass=$((nopass+1)); ko "sans passphrase : $(basename "$k")"; fi
done
[ "$nopass" -eq 0 ] && ok "toutes les clés SSH ont une passphrase"

hr; echo "[4] Fichiers de credentials en clair"
for f in "$HOME/.git-credentials" "$HOME/.netrc" "$HOME/.config/gh/hosts.yml" "$HOME/.aws/credentials"; do
  [ -e "$f" ] && ko "présent en clair : ${f/#$HOME/\~}  (perms $(stat -c %a "$f" 2>/dev/null))"
done

hr; echo "[5] Fichiers .env en clair (paires clé=valeur)"
envc=0
while IFS= read -r f; do
  if grep -qE '^[A-Za-z_]+=.+' "$f" 2>/dev/null; then envc=$((envc+1)); fi
done < <(find "$HOME" -maxdepth 4 -name '*.env' -o -maxdepth 4 -name '.env' 2>/dev/null | grep -v node_modules | grep -v '/.antigravity/')
if [ "$envc" -gt 0 ]; then ko "$envc fichier(s) .env avec secrets EN CLAIR"; else ok "aucun .env en clair"; fi

hr; echo "[6] Secret store chiffré (SOPS/age) en place ?"
if command -v sops >/dev/null && command -v age >/dev/null; then ok "sops + age installés"; else wn "sops/age non installés (secret store chiffré pas encore en place)"; fi
[ -f "$HOME/.config/sops/age/keys.txt" ] && ok "clé age présente" || wn "pas de clé age"

hr; echo "[7] Secrets en clair commités dans un repo git ?"
leak=0
while IFS= read -r g; do
  d="$(dirname "$g")"
  if git -C "$d" grep -IlE '(ghp_[A-Za-z0-9]{20}|api[_-]?key|secret|password)=' -- . >/dev/null 2>&1; then leak=$((leak+1)); fi
done < <(find "$HOME" -maxdepth 3 -name .git -type d 2>/dev/null | grep -v node_modules)
[ "$leak" -gt 0 ] && wn "$leak repo(s) à inspecter pour secrets commités" || ok "aucun secret évident commité"

hr; echo "=== Fin. Cible après durcissement : tout en ${GRN}✓${RST} ou ${YEL}!${RST}, zéro ${RED}✗${RST}. ==="
