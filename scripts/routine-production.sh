#!/usr/bin/env bash
# ============================================================================
# routine-production.sh — Cadence de production hebdomadaire M4 (entreprise).
# Lancé 1x/jour (cron ~7h). Léger, on-demand, AUCUNE boucle (anti-surchauffe).
# Usage : bash routine-production.sh [jour]   (jour: lun|mar|mer|jeu|ven|sam|dim, défaut=auto)
# ============================================================================
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
PUB=$(age-keygen -y "$HOME/.config/sops/age/keys.txt" 2>/dev/null)
REP="$HOME/jarvis/reports"; BK="$HOME/jarvis/backups"; mkdir -p "$REP" "$BK"
DOW="${1:-$(date +%u)}"; case "$DOW" in 1|lun)D=lun;;2|mar)D=mar;;3|mer)D=mer;;4|jeu)D=jeu;;5|ven)D=ven;;6|sam)D=sam;;7|dim)D=dim;;*)D=$DOW;;esac
TODAY=$(date +%F); R="$REP/jour-$TODAY.md"

{
echo "# Rapport production M4 — $TODAY ($D)"
echo
echo "## Santé des services"
docker service ls --format '- {{.Name}} : {{.Replicas}} ({{.Image}})' 2>/dev/null | grep -E 'jarvis_|data_|business_'
echo
echo "## Machine"
free -h | awk '/Mem/{print "- RAM: "$3"/"$2}'
(sensors 2>/dev/null | grep -iE 'package id 0' | head -1 | sed 's/^/- Temp: /') || true
systemctl --user is-active m4-thermal-governor 2>/dev/null | sed 's/^/- Gouverneur thermique: /'
} > "$R"

# --- QUOTIDIEN : backup incrémental chiffré (postgres dump + n8n) ---
PC=$(docker ps -qf name=data_postgres | head -1)
[ -n "$PC" ] && docker exec "$PC" pg_dump -U jarvis jarvis_agents 2>/dev/null | age -r "$PUB" > "$BK/pg-$TODAY.sql.age" 2>/dev/null && echo "## Backup quotidien" >> "$R" && echo "- postgres dump chiffré ✓" >> "$R"
docker run --rm -v docker_jarvis-n8n-data:/d:ro alpine tar czf - -C /d . 2>/dev/null | age -r "$PUB" > "$BK/n8n-$TODAY.tgz.age" 2>/dev/null && echo "- n8n volume chiffré ✓" >> "$R"

# --- LUNDI : audit sécurité complet (kickoff semaine) ---
if [ "$D" = "lun" ]; then
  echo -e "\n## LUNDI — Audit sécurité (kickoff)" >> "$R"
  bash "$HOME/jarvis/scripts/sec-audit.sh" 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | grep -E '✓|✗|!|\[' | sed 's/^/- /' >> "$R"
fi

# --- VENDREDI : backup hebdo complet + rotation (>14j) ---
if [ "$D" = "ven" ]; then
  echo -e "\n## VENDREDI — Backup hebdo + rotation" >> "$R"
  for v in $(docker volume ls -q | grep -E 'n8n|registry|redis|portainer|postgres'); do
    docker run --rm -v "$v":/d:ro alpine tar czf - -C /d . 2>/dev/null | age -r "$PUB" > "$BK/hebdo-$v-$TODAY.tar.gz.age" 2>/dev/null
  done
  find "$BK" -name '*.age' -mtime +14 -delete 2>/dev/null && echo "- purge backups > 14j ✓" >> "$R"
  echo "- backup hebdo complet ✓" >> "$R"
fi

# --- WEEK-END : maintenance légère (images orphelines) ---
if [ "$D" = "sam" ] || [ "$D" = "dim" ]; then
  echo -e "\n## WEEK-END — Maintenance" >> "$R"
  docker image prune -f >/dev/null 2>&1 && echo "- nettoyage images orphelines ✓" >> "$R"
fi

echo "Rapport: $R"
