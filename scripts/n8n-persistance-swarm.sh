#!/usr/bin/env bash
# Rend PERSISTANTES les données n8n du service Swarm jarvis-full-stack_n8n.
#
# CONTEXTE (établi par investigation, 2026-08-01) :
#   Le service ne déclare AUCUN volume — sa base vit dans la couche inscriptible
#   du conteneur (/home/node/.n8n/database.sqlite, 1,5 Mo). Toute recréation de
#   conteneur (update, reboot, replanification) l'efface sans avertissement.
#
# LE PIÈGE QUE CE SCRIPT ÉVITE :
#   Monter un volume sur /home/node/.n8n MASQUE la base existante. Le volume
#   jarvis_n8n_data qui traîne sur rem-linux contient un database.sqlite de
#   0 OCTET — le monter tel quel ferait démarrer n8n sur une base VIDE.
#   D'où l'ordre imposé : extraire d'abord, semer, monter enfin.
#
# Épinglage : le service reste sur le nœud où il tourne déjà (changement minimal).
# Le rééquilibrage de charge est une décision distincte, hors périmètre ici.
set -euo pipefail

SERVICE="jarvis-full-stack_n8n"
MANAGER="jarvis-dva"                 # alias SSH du Leader Swarm (rem-linux)
DATA_PATH="/home/node/.n8n"
VOLUME="n8n_persist_data"            # volume neuf : on ne réutilise pas le vide
TS="$(date +%Y%m%d_%H%M%S)"

say() { printf '\n=== %s\n' "$*"; }
die() { printf '\nÉCHEC : %s\n' "$*" >&2; exit 1; }

# ---------------------------------------------------------------- 1. localiser
say "1/6  Localisation du nœud et du conteneur"
NODE=$(ssh -o BatchMode=yes "$MANAGER" \
  "docker service ps $SERVICE --filter desired-state=running --format '{{.Node}}'" \
  2>/dev/null | head -1)
[ -n "$NODE" ] || die "service $SERVICE introuvable ou sans tâche en cours"
echo "  nœud    : $NODE"

# Alias SSH du nœud cible (le manager s'atteint autrement que le worker).
case "$NODE" in
  rem-linux)         NODE_SSH="jarvis-dva" ;;
  serveurremjarvis)  NODE_SSH="remjarvis-root" ;;
  *) die "nœud inconnu : $NODE — ajouter son alias SSH avant de continuer" ;;
esac

CID=$(ssh -o BatchMode=yes "$NODE_SSH" \
  "docker ps --filter name=${SERVICE} --format '{{.Names}}'" 2>/dev/null | head -1)
[ -n "$CID" ] || die "conteneur n8n introuvable sur $NODE"
echo "  conteneur : ${CID:0:46}"

# ------------------------------------------------------- 2. garde-fou données
say "2/6  Vérification que la base vivante est non vide"
SIZE=$(ssh -o BatchMode=yes "$NODE_SSH" \
  "docker exec '$CID' stat -c %s $DATA_PATH/database.sqlite" 2>/dev/null || echo 0)
echo "  database.sqlite : $SIZE octets"
[ "$SIZE" -gt 100000 ] || die "base vide ou illisible ($SIZE o) — on n'écrase rien, arrêt"

# --------------------------------------------------------- 3. extraction sûre
# docker cp lit la couche du conteneur : c'est la SEULE copie des workflows.
say "3/6  Extraction de la base vers l'hôte (avant tout montage)"
BACKUP="/root/n8n-avant-persistance-$TS.tar"
ssh -o BatchMode=yes "$NODE_SSH" \
  "docker cp '$CID:$DATA_PATH' /tmp/n8n-$TS && tar -cf '$BACKUP' -C /tmp n8n-$TS && rm -rf /tmp/n8n-$TS" \
  || die "extraction impossible — ARRÊT, aucune modification faite"
BSIZE=$(ssh -o BatchMode=yes "$NODE_SSH" "stat -c %s '$BACKUP'" 2>/dev/null || echo 0)
echo "  sauvegarde : $BACKUP ($((BSIZE/1024)) Ko)"
[ "$BSIZE" -gt 100000 ] || die "sauvegarde suspecte ($BSIZE o) — arrêt"

# ------------------------------------------------------------ 4. semer volume
say "4/6  Création et amorçage du volume $VOLUME sur $NODE"
ssh -o BatchMode=yes "$NODE_SSH" "docker volume create '$VOLUME' >/dev/null" \
  || die "création du volume impossible"
# Conteneur jetable : recopie l'arborescence extraite DANS le volume.
ssh -o BatchMode=yes "$NODE_SSH" "
  mkdir -p /tmp/seed-$TS && tar -xf '$BACKUP' -C /tmp/seed-$TS &&
  docker run --rm -v '$VOLUME':/dest -v /tmp/seed-$TS/n8n-$TS:/src:ro alpine \
    sh -c 'cp -a /src/. /dest/ && chown -R 1000:1000 /dest' &&
  rm -rf /tmp/seed-$TS
" || die "amorçage du volume impossible"

SEEDED=$(ssh -o BatchMode=yes "$NODE_SSH" \
  "docker run --rm -v '$VOLUME':/d alpine stat -c %s /d/database.sqlite" 2>/dev/null || echo 0)
echo "  base dans le volume : $SEEDED octets"
[ "$SEEDED" = "$SIZE" ] || die "taille divergente (volume $SEEDED ≠ conteneur $SIZE) — arrêt AVANT le montage"

# ------------------------------------------------- 5. montage + épinglage
# Une seule commande : jamais d'instant où le volume serait monté sans épinglage,
# ce qui laisserait Swarm replanifier ailleurs et créer un volume VIDE.
say "5/6  Montage du volume et épinglage sur $NODE"
ssh -o BatchMode=yes "$MANAGER" "docker service update \
  --constraint-add 'node.hostname==$NODE' \
  --mount-add type=volume,source=$VOLUME,target=$DATA_PATH \
  --update-order start-first \
  $SERVICE" || die "mise à jour du service refusée — données intactes dans $BACKUP"

# ------------------------------------------------------------- 6. vérification
say "6/6  Vérification"
sleep 15
ssh -o BatchMode=yes "$MANAGER" "docker service ls --filter name=$SERVICE"
NEW=$(ssh -o BatchMode=yes "$NODE_SSH" "
  C=\$(docker ps --filter name=$SERVICE --format '{{.Names}}' | head -1)
  docker exec \"\$C\" stat -c %s $DATA_PATH/database.sqlite 2>/dev/null" || echo 0)
echo "  database.sqlite après montage : $NEW octets (avant : $SIZE)"
[ "$NEW" = "$SIZE" ] && echo "  ✅ données préservées" \
                     || echo "  ⚠️  ÉCART — restaurer depuis $BACKUP sur $NODE"
echo
echo "Sauvegarde conservée : $NODE:$BACKUP"
