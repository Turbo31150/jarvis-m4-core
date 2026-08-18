#!/usr/bin/env bash
# Migre les 7 services Swarm de serveurremjarvis vers rem-linux (manager).
# Familles :
#   A) sans données  (litellm, redis-replica)            → swap de contraintes
#   B) volatiles avec données (prometheus:/prometheus, loki:/loki)
#      → extraire du conteneur vivant, semer volume sur rem-linux, mount+swap
#   C) persistés sqlite (n8n, grafana, vaultwarden)
#      → scale 0 (cohérence sqlite), copier le volume, swap, scale 1
# Toute étape échouée = arrêt du service concerné, les autres continuent.
set -u
MGR="jarvis-dva"          # rem-linux, manager Swarm (docker local)
WRK="remjarvis-root"      # serveurremjarvis, worker
say(){ printf '\n=== %s\n' "$*"; }
ko(){ printf '  !! %s\n' "$*"; }

swap_constraints(){ # $1=service
  ssh -o BatchMode=yes "$MGR" "docker service update -d \
    --constraint-rm 'node.role == worker' \
    --constraint-rm 'node.hostname==serveurremjarvis' \
    --constraint-add 'node.hostname==rem-linux' '$1'" >/dev/null 2>&1
  # doublon éventuel de la contrainte hostname (vu sur grafana/n8n)
  ssh -o BatchMode=yes "$MGR" "docker service update -d \
    --constraint-rm 'node.hostname==serveurremjarvis' '$1'" >/dev/null 2>&1 || true
}

copy_volume(){ # $1=volume  — worker → manager via M1 (tar pipe)
  ssh -o BatchMode=yes "$MGR" "docker volume create '$1' >/dev/null" || return 1
  ssh -o BatchMode=yes "$WRK" "docker run --rm -v '$1':/d alpine tar -cf - -C /d ." \
    | ssh -o BatchMode=yes "$MGR" "docker run --rm -i -v '$1':/d alpine tar -xf - -C /d" || return 1
  return 0
}

wait_running(){ # $1=service — attend une tâche running sur rem-linux
  for i in $(seq 1 30); do
    N=$(ssh -o BatchMode=yes "$MGR" "docker service ps '$1' --filter desired-state=running --format '{{.Node}} {{.CurrentState}}'" 2>/dev/null | head -1)
    case "$N" in rem-linux\ Running*) echo "  ✅ $1 → rem-linux ($N)"; return 0;; esac
    sleep 4
  done
  ko "$1 : pas Running sur rem-linux après 120s — état: $N"; return 1
}

# ---------- A) sans données ----------
for S in jarvis-full-stack_litellm jarvis-tanker_redis-replica; do
  say "A · $S — swap de contraintes"
  swap_constraints "$S"; wait_running "$S"
done

# ---------- B) volatiles avec données ----------
migrate_volatile(){ # $1=service $2=data_path $3=volume $4=uid:gid
  say "B · $1 — extraction $2 → volume $3 sur rem-linux"
  CID=$(ssh -o BatchMode=yes "$WRK" "docker ps --filter name=$1 --format '{{.Names}}'" | head -1)
  if [ -z "$CID" ]; then ko "$1 : conteneur introuvable sur worker, swap simple"; swap_constraints "$1"; wait_running "$1"; return; fi
  ssh -o BatchMode=yes "$MGR" "docker volume create '$3' >/dev/null"
  ssh -o BatchMode=yes "$WRK" "docker exec '$CID' tar -cf - -C '$2' . 2>/dev/null || docker cp '$CID:$2' - " \
    | ssh -o BatchMode=yes "$MGR" "docker run --rm -i -v '$3':/d alpine sh -c 'tar -xf - -C /d && chown -R $4 /d'" \
    || { ko "$1 : extraction échouée — service laissé en place"; return; }
  SZ=$(ssh -o BatchMode=yes "$MGR" "docker run --rm -v '$3':/d alpine du -sb /d | cut -f1")
  echo "  volume semé : $SZ octets"
  ssh -o BatchMode=yes "$MGR" "docker service update -d \
    --mount-add type=volume,source=$3,target=$2 '$1'" >/dev/null 2>&1
  swap_constraints "$1"; wait_running "$1"
}
migrate_volatile jarvis-full-stack_prometheus /prometheus prometheus_persist_data 65534:65534
migrate_volatile jarvis-full-stack_loki       /loki       loki_persist_data       10001:10001

# ---------- C) persistés sqlite ----------
migrate_persisted(){ # $1=service $2=volume
  say "C · $1 — scale 0 → copie volume $2 → swap → relance"
  ssh -o BatchMode=yes "$MGR" "docker service scale -d '$1'=0" >/dev/null 2>&1
  sleep 8
  copy_volume "$2" || { ko "$1 : copie volume échouée — retour scale 1 sur place"; ssh -o BatchMode=yes "$MGR" "docker service scale -d '$1'=1" >/dev/null; return; }
  SZ=$(ssh -o BatchMode=yes "$MGR" "docker run --rm -v '$2':/d alpine du -sb /d | cut -f1")
  echo "  volume copié sur rem-linux : $SZ octets"
  swap_constraints "$1"
  ssh -o BatchMode=yes "$MGR" "docker service scale -d '$1'=1" >/dev/null 2>&1
  wait_running "$1"
}
migrate_persisted jarvis-full-stack_n8n     n8n_persist_data
migrate_persisted jarvis-full-stack_grafana jarvis-full-stack_grafana_persist
migrate_persisted jarvis-tanker_vaultwarden vaultwarden_persist_data

say "État final"
ssh -o BatchMode=yes "$MGR" "docker service ls --format '{{.Name}}\t{{.Replicas}}'"
ssh -o BatchMode=yes "$MGR" "docker service ps jarvis-full-stack_n8n jarvis-full-stack_grafana jarvis-tanker_vaultwarden jarvis-full-stack_prometheus jarvis-full-stack_loki jarvis-full-stack_litellm jarvis-tanker_redis-replica --filter desired-state=running --format '{{.Name}}\t{{.Node}}\t{{.CurrentState}}' 2>/dev/null | sort -u"
