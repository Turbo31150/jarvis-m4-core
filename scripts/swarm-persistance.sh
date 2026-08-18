#!/usr/bin/env bash
# Rend PERSISTANTES les données d'un service Swarm qui tourne en stockage volatil.
#
# Usage :
#   swarm-persistance.sh jarvis-full-stack_n8n     /home/node/.n8n    1000:1000
#   swarm-persistance.sh jarvis-full-stack_grafana /var/lib/grafana   472:0
#
# CONTEXTE (investigation 2026-08-01) : aucun service de la pile jarvis-full-stack
# ne déclare de volume. Leurs données vivent dans la couche inscriptible du
# conteneur — toute recréation (update, reboot, replanification) les efface.
#
# LE PIÈGE QUE CE SCRIPT ÉVITE : monter un volume sur le répertoire de données
# MASQUE la base existante. Un volume préexistant peut contenir une base VIDE
# (cas vérifié : jarvis_n8n_data contenait un database.sqlite de 0 octet).
# D'où l'ordre imposé : extraire d'abord, semer, vérifier, monter enfin.
#
# Épinglage : le service reste sur le nœud où il tourne déjà. Un volume `local`
# n'existe que sur un nœud ; sans épinglage, Swarm peut replanifier ailleurs et
# créer un volume VIDE du même nom. Le rééquilibrage de charge est hors périmètre.
set -euo pipefail

SERVICE="${1:?usage: $0 <service> <chemin-donnees> [uid:gid]}"
DATA_PATH="${2:?usage: $0 <service> <chemin-donnees> [uid:gid]}"
OWNER="${3:-}"                       # vide = on ne touche pas aux permissions
MANAGER="jarvis-dva"                 # alias SSH du Leader Swarm (rem-linux)
VOLUME="$(basename "$SERVICE")_persist"
TS="$(date +%Y%m%d_%H%M%S)"
MIN_BYTES=${MIN_BYTES:-50000}        # garde-fou : sous ce seuil, on refuse d'agir

say() { printf '\n=== %s\n' "$*"; }
die() { printf '\nÉCHEC : %s\n' "$*" >&2; exit 1; }

say "Service : $SERVICE    Données : $DATA_PATH    Volume : $VOLUME"

# ---------------------------------------------------------------- 1. localiser
say "1/6  Localisation du nœud et du conteneur"
NODE=$(ssh -o BatchMode=yes "$MANAGER" \
  "docker service ps $SERVICE --filter desired-state=running --format '{{.Node}}'" \
  2>/dev/null | head -1)
[ -n "$NODE" ] || die "service $SERVICE introuvable ou sans tâche en cours"

case "$NODE" in
  rem-linux)         NODE_SSH="jarvis-dva" ;;
  serveurremjarvis)  NODE_SSH="remjarvis-root" ;;
  *) die "nœud inconnu : $NODE — ajouter son alias SSH avant de continuer" ;;
esac
CID=$(ssh -o BatchMode=yes "$NODE_SSH" \
  "docker ps --filter name=${SERVICE} --format '{{.Names}}'" 2>/dev/null | head -1)
[ -n "$CID" ] || die "conteneur introuvable sur $NODE"
echo "  nœud $NODE — conteneur ${CID:0:46}"

# --------------------------------------------------- 2. garde-fou sur la taille
# On mesure le répertoire entier : tous les services n'ont pas un fichier unique.
say "2/6  Vérification que les données sont non vides"
SIZE=$(ssh -o BatchMode=yes "$NODE_SSH" \
  "docker exec '$CID' du -sb '$DATA_PATH' 2>/dev/null | cut -f1" || echo 0)
echo "  taille mesurée : $SIZE octets"
[ "${SIZE:-0}" -gt "$MIN_BYTES" ] || die "données vides ou illisibles ($SIZE o) — on n'écrase rien, arrêt"

# --------------------------------------------------------- 3. extraction sûre
# docker cp lit la couche du conteneur : c'est la SEULE copie de ces données.
say "3/6  Extraction vers l'hôte (avant tout montage)"
BACKUP="/root/${SERVICE}-avant-persistance-$TS.tar"
ssh -o BatchMode=yes "$NODE_SSH" \
  "docker cp '$CID:$DATA_PATH' /tmp/seed-$TS && tar -cf '$BACKUP' -C /tmp seed-$TS" \
  || die "extraction impossible — ARRÊT, aucune modification faite"
BSIZE=$(ssh -o BatchMode=yes "$NODE_SSH" "stat -c %s '$BACKUP'" 2>/dev/null || echo 0)
echo "  sauvegarde : $NODE:$BACKUP ($((BSIZE/1024)) Ko)"
[ "${BSIZE:-0}" -gt "$MIN_BYTES" ] || die "sauvegarde suspecte ($BSIZE o) — arrêt"

# ------------------------------------------------------------ 4. semer volume
say "4/6  Création et amorçage du volume $VOLUME sur $NODE"
ssh -o BatchMode=yes "$NODE_SSH" "docker volume create '$VOLUME' >/dev/null" \
  || die "création du volume impossible"
CHOWN=""
[ -n "$OWNER" ] && CHOWN=" && chown -R $OWNER /dest"
ssh -o BatchMode=yes "$NODE_SSH" "
  docker run --rm -v '$VOLUME':/dest -v /tmp/seed-$TS:/src:ro alpine \
    sh -c 'cp -a /src/. /dest/${CHOWN}' && rm -rf /tmp/seed-$TS
" || die "amorçage du volume impossible — données intactes dans $BACKUP"

SEEDED=$(ssh -o BatchMode=yes "$NODE_SSH" \
  "docker run --rm -v '$VOLUME':/d alpine du -sb /d | cut -f1" 2>/dev/null || echo 0)
echo "  volume amorcé : $SEEDED octets (source : $SIZE)"
# Tolérance 2 % : le format du volume diffère légèrement de la couche conteneur.
python3 - "$SIZE" "$SEEDED" <<'PY' || die "écart de taille trop important — arrêt AVANT le montage"
import sys
src, dst = int(sys.argv[1]), int(sys.argv[2])
sys.exit(0 if dst >= src * 0.98 else 1)
PY

# ------------------------------------------------- 5. montage + épinglage
# Une SEULE commande : jamais d'instant où le volume serait monté sans épinglage.
say "5/6  Montage du volume et épinglage sur $NODE"
ssh -o BatchMode=yes "$MANAGER" "docker service update \
  --constraint-add 'node.hostname==$NODE' \
  --mount-add type=volume,source=$VOLUME,target=$DATA_PATH \
  --update-order start-first \
  $SERVICE" || die "mise à jour refusée — données intactes dans $NODE:$BACKUP"

# ------------------------------------------------------------- 6. vérification
say "6/6  Vérification"
sleep 15
ssh -o BatchMode=yes "$MANAGER" "docker service ls --filter name=$SERVICE"
NEW=$(ssh -o BatchMode=yes "$NODE_SSH" "
  C=\$(docker ps --filter name=$SERVICE --format '{{.Names}}' | head -1)
  docker exec \"\$C\" du -sb '$DATA_PATH' 2>/dev/null | cut -f1" || echo 0)
echo "  taille après montage : $NEW octets (avant : $SIZE)"
python3 - "$SIZE" "${NEW:-0}" <<'PY' && echo "  ✅ données préservées" || echo "  ⚠️  ÉCART — restaurer depuis $BACKUP sur $NODE"
import sys
src, now = int(sys.argv[1]), int(sys.argv[2])
sys.exit(0 if now >= src * 0.98 else 1)
PY
echo
echo "Sauvegarde conservée : $NODE:$BACKUP"
