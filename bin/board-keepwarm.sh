#!/usr/bin/env bash
# board-keepwarm.sh — garde le backend du Board OS pret a servir, en continu.
#
# Verifie que le noeud du cable direct a bien CHARGE les deux modeles dont le
# board depend : le chat ET l'embedding (sans ce dernier, la voie vectorielle
# retombe en http_400 et le board degrade en FTS5 seul).
#
# REGLE DE SURETE — n'agir que sur une sonde CERTAINE.
# La source de verite est `lms ps` en SSH, pas l'endpoint HTTP /v1/models :
# ce dernier renvoie une liste VIDE quand le serveur traite une requete, et
# n'expose de toute facon pas les modeles d'embedding. S'y fier faisait
# conclure "tout est absent" et rechargeait le chat en boucle, empilant des
# instances :2, :3... jusqu'a saturer la VRAM. En cas de sonde douteuse on ne
# charge RIEN : mieux vaut ne pas agir que dupliquer.
set -uo pipefail

NODE=10.42.0.230
CHAT_MODEL="qwen/qwen3.5-9b"
EMBED_MODEL="text-embedding-nomic-embed-text-v1.5"
SSH_TARGET="turbo@$NODE"
SSH_OPTS=(-o IdentityAgent=none -o BatchMode=yes -o ConnectTimeout=8)
REMOTE_PATH='export PATH=$PATH:$HOME/.lmstudio/bin;'
LOG=~/jarvis/logs/board-keepwarm.log
INTERVAL=120

mkdir -p "$(dirname "$LOG")"
log(){ printf '%s %s\n' "$(date '+%F %T')" "$*" >>"$LOG"; }

# Renvoie les IDENTIFIER charges, un par ligne. Code retour non nul = sonde ratee.
sonde() {
  local out
  out=$(timeout 30 ssh "${SSH_OPTS[@]}" "$SSH_TARGET" "$REMOTE_PATH lms ps 2>/dev/null") || return 1
  grep -q IDENTIFIER <<<"$out" || return 1        # en-tete absent = sortie inexploitable
  # Une ligne vide precede le tableau : filtrer l'en-tete par son nom, pas par NR.
  awk '$1!="" && $1!="IDENTIFIER" {print $1}' <<<"$out"
}

# Contexte du modele de chat. A 4096 (defaut d'un rechargement nu), les prompts
# du board -- consigne d'expert + 6 extraits de corpus -- depassent la fenetre :
# 2 experts sur 4 tombaient en PANNE BACKEND et la deliberation prenait 71 s.
# A 32768 : 0 panne, 37 s. Mesure le 2026-08-15 sur question identique.
CTX_CHAT=32768

charger() {
  log "chargement demande : $1"
  local opts=""
  [ "$1" = "$CHAT_MODEL" ] && opts="--context-length $CTX_CHAT"
  if timeout 240 ssh "${SSH_OPTS[@]}" "$SSH_TARGET" "$REMOTE_PATH lms load '$1' $opts --yes" >/dev/null 2>&1; then
    log "charge OK : $1"
  else
    log "ECHEC chargement : $1"
  fi
}

log "demarrage keep-warm (uid=$(id -u) $(id -un)) noeud=$NODE intervalle=${INTERVAL}s"
etat_precedent=""
while :; do
  if ! charges=$(sonde); then
    [ "$etat_precedent" != "SONDE_KO" ] && log "sonde lms ps INDISPONIBLE — aucune action (pas de chargement a l'aveugle)"
    etat_precedent="SONDE_KO"
    sleep "$INTERVAL"; continue
  fi

  # Doublons = meme modele charge plusieurs fois (identifiants suffixes :2, :3...).
  doublons=$(grep -E ':[0-9]+$' <<<"$charges" || true)
  if [ -n "$doublons" ]; then
    log "DOUBLONS detectes, dechargement : $(tr '\n' ' ' <<<"$doublons")"
    while read -r d; do
      [ -n "$d" ] && timeout 60 ssh "${SSH_OPTS[@]}" "$SSH_TARGET" \
        "$REMOTE_PATH lms unload '$d'" >/dev/null 2>&1 && log "decharge : $d"
    done <<<"$doublons"
  fi

  # Contexte du chat : present ne suffit pas, il doit etre au BON contexte.
  # LM Studio recharge le modele en JIT a la premiere requete d'un client
  # (ici la boucle de supervision, toutes les 15 min) avec ses defauts a 4096 —
  # ce qui refait tomber 2 experts sur 4. Un keep-warm qui ne teste que la
  # presence laisse donc le reglage se faire ecraser indefiniment.
  ctx_actuel=$(timeout 30 ssh "${SSH_OPTS[@]}" "$SSH_TARGET" \
    "$REMOTE_PATH lms ps 2>/dev/null" \
    | awk -v m="$CHAT_MODEL" '$1==m{for(i=1;i<=NF;i++) if($i=="GB"||$i=="MB"){print $(i+1); exit}}' | head -1)
  # Ne JAMAIS recharger un modele en train de servir : le decharger coupe la
  # requete en cours (« Model is unloaded » cote client) et le rechargement
  # prend plusieurs minutes. Constate le 2026-08-17 : le board tombait en
  # 4 pannes sur 4 parce que ce keep-warm rechargeait pendant sa deliberation.
  statut=$(timeout 30 ssh "${SSH_OPTS[@]}" "$SSH_TARGET" \
    "$REMOTE_PATH lms ps 2>/dev/null" | awk -v m="$CHAT_MODEL" '$1==m{print $3; exit}')
  if [ "$statut" != "IDLE" ] && [ -n "$statut" ]; then
    [ "$etat_precedent" != "OCCUPE" ] && log "modele occupe ($statut) — aucune action"
    etat_precedent="OCCUPE"
    sleep "$INTERVAL"; continue
  fi

  if [ -n "$ctx_actuel" ] && [ "$ctx_actuel" != "$CTX_CHAT" ]; then
    log "contexte chat degrade : $ctx_actuel (attendu $CTX_CHAT) — rechargement"
    timeout 60 ssh "${SSH_OPTS[@]}" "$SSH_TARGET" \
      "$REMOTE_PATH lms unload '$CHAT_MODEL'" >/dev/null 2>&1
    charger "$CHAT_MODEL"
    sleep "$INTERVAL"; continue
  fi

  manquants=""
  for m in "$CHAT_MODEL" "$EMBED_MODEL"; do
    grep -qxF "$m" <<<"$charges" || manquants+="$m "
  done

  if [ -n "$manquants" ]; then
    log "modele(s) absent(s) : $manquants"
    for m in $manquants; do charger "$m"; done
  elif [ "$etat_precedent" != "OK" ]; then
    log "nominal : chat + embedding charges, aucun doublon"
  fi
  etat_precedent=$([ -n "$manquants" ] && echo "MANQUE" || echo "OK")
  sleep "$INTERVAL"
done
