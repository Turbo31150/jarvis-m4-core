#!/usr/bin/env bash
# ============================================================================
# cascade-harden-kit.sh — Durcissement « coffre secrets chiffré » (sops+age)
# MÊME méthode/protocole que M4. Idempotent : ré-exécutable sans risque.
# Déploiement sur un nœud (M1/M2/M5) une fois allumé :
#     ssh m1 'bash -s' < ~/jarvis/scripts/cascade-harden-kit.sh
#   ou, en local sur le nœud :  bash cascade-harden-kit.sh
# Ne révoque rien, n'exfiltre rien, ne supprime aucun .env en clair.
# ============================================================================
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
RED=$'\e[31m'; GRN=$'\e[32m'; YEL=$'\e[33m'; RST=$'\e[0m'
ko(){ echo "${RED}✗ $*${RST}"; }; ok(){ echo "${GRN}✓ $*${RST}"; }; wn(){ echo "${YEL}! $*${RST}"; }
hr(){ printf '%s\n' "──────────────────────────────────────────────"; }
AGEV=v1.2.1; SOPSV=v3.9.4
KEYFILE="$HOME/.config/sops/age/keys.txt"; VAULT="$HOME/jarvis/secrets-vault"

echo "=== CASCADE-HARDEN sur $(hostname) — $(date '+%F %T') ==="

audit(){
  hr; echo "[AUDIT $1]"
  lsblk -o FSTYPE 2>/dev/null | grep -qi crypt && ok "disque chiffré" || ko "disque NON chiffré"
  local c=0; while IFS= read -r d; do file -b "$d" 2>/dev/null | grep -qi "SQLite 3" && c=$((c+1)); done \
    < <(find "$HOME" -maxdepth 5 \( -name '*.db' -o -name '*.sqlite*' \) 2>/dev/null | grep -v node_modules)
  [ "$c" -gt 0 ] && ko "$c base(s) SQLite en clair" || ok "0 base SQLite en clair"
  local e=0; while IFS= read -r f; do grep -qE '^[A-Za-z_]+=.+' "$f" 2>/dev/null && e=$((e+1)); done \
    < <(find "$HOME" -maxdepth 4 -name '*.env' 2>/dev/null | grep -v node_modules | grep -v '/.antigravity/')
  [ "$e" -gt 0 ] && ko "$e .env en clair" || ok "0 .env en clair"
  command -v sops >/dev/null && command -v age >/dev/null && ok "sops+age présents" || wn "sops/age absents"
  [ -f "$KEYFILE" ] && ok "clé age présente" || wn "pas de clé age"
}

audit AVANT

hr; echo "[1] Installer age + sops (si absents, sans sudo)"
if ! command -v age >/dev/null; then
  curl -fsSL -o /tmp/age.tgz "https://github.com/FiloSottile/age/releases/download/$AGEV/age-$AGEV-linux-amd64.tar.gz" \
    && tar -C /tmp -xzf /tmp/age.tgz && mkdir -p "$HOME/.local/bin" \
    && install -m755 /tmp/age/age /tmp/age/age-keygen "$HOME/.local/bin/" && rm -rf /tmp/age /tmp/age.tgz \
    && ok "age installé" || ko "échec install age (réseau ?)"
else ok "age déjà là"; fi
if ! command -v sops >/dev/null; then
  curl -fsSL -o "$HOME/.local/bin/sops" "https://github.com/getsops/sops/releases/download/$SOPSV/sops-$SOPSV.linux.amd64" \
    && chmod 755 "$HOME/.local/bin/sops" && ok "sops installé" || ko "échec install sops"
else ok "sops déjà là"; fi

hr; echo "[2] Clé age (générée 1x, jamais écrasée)"
mkdir -p "$(dirname "$KEYFILE")"
if [ ! -f "$KEYFILE" ]; then age-keygen -o "$KEYFILE" 2>/dev/null && chmod 600 "$KEYFILE" && ok "clé age créée (À SAUVER HORS-LIGNE)"; else ok "clé age existante conservée"; fi
PUB=$(age-keygen -y "$KEYFILE")

hr; echo "[3] Coffre + chiffrement des .env sensibles"
mkdir -p "$VAULT"; cd "$VAULT"
printf '%s\n' '*.key' 'keys.txt' '*.env' '!*.enc.env' > .gitignore
i=0
while IFS= read -r f; do
  grep -qE '^[A-Za-z_]+=.+' "$f" 2>/dev/null || continue
  base=$(echo "$f" | sed "s#$HOME/##; s#[/.]#_#g"); out="${base}.enc.env"
  [ -f "$out" ] && continue
  cp "$f" "$out"
  if SOPS_AGE_KEY_FILE="$KEYFILE" sops -e -i --input-type dotenv --output-type dotenv "$out" 2>/dev/null; then
    i=$((i+1)); echo "  ✓ $out ($(grep -cE 'ENC\[' "$out") secrets)"
  else rm -f "$out"; fi
done < <(find "$HOME" -maxdepth 4 -name '*.env' 2>/dev/null | grep -v node_modules | grep -v '/.antigravity/' | grep -v "$VAULT")
ok "$i fichier(s) chiffré(s) dans le coffre"

hr; echo "[4] Verrouiller les .env en clair (chmod 600)"
n=0; while IFS= read -r f; do chmod 600 "$f" 2>/dev/null && n=$((n+1)); done \
  < <(find "$HOME" -maxdepth 4 -name '*.env' 2>/dev/null | grep -v node_modules | grep -v '/.antigravity/'); ok "$n .env en 600"

audit APRÈS
hr; echo "${GRN}Terminé.${RST} Coffre: $VAULT  | Clé: $KEYFILE (À SAUVEGARDER HORS-LIGNE)."
echo "Rappel: brancher les services sur le coffre PUIS supprimer les .env en clair. Vague 3 (SQLCipher) + Vague 4 (backup hors-ligne) restent à faire."
