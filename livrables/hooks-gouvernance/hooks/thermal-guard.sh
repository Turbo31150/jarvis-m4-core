#!/usr/bin/env bash
# thermal-guard.sh — hook PreToolUse : bloque l'exécution si le CPU dépasse le
# seuil thermique du M4 (garde-fou surchauffe, cohérent avec m4-thermal-governor).
# Sortie exit 2 = bloque l'outil et renvoie le message à Claude ; exit 0 = laisse passer.
# 0-token, lecture pure de /sys. Fail-safe : toute erreur → laisse passer.
set -uo pipefail

SEUIL_MC=90000   # 90 °C en milli-degrés (coupure ; le governor vise déjà 82 °C)
LOG="${HOME}/jarvis/logs/thermal-guard.log"
mkdir -p "$(dirname "$LOG")" 2>/dev/null || true

max=0
for z in /sys/class/thermal/thermal_zone*/temp; do
  [ -r "$z" ] || continue
  v=$(cat "$z" 2>/dev/null) || continue
  [ "$v" -gt "$max" ] 2>/dev/null && max=$v
done

if [ "$max" -ge "$SEUIL_MC" ] 2>/dev/null; then
  deg=$((max/1000))
  echo "$(date -Is)	BLOCK	${deg}C" >> "$LOG"
  echo "⛔ Garde thermique : CPU à ${deg}°C (seuil ${SEUIL_MC%000}°C). Exécution suspendue — laisse refroidir ou vérifie m4-thermal-governor." >&2
  exit 2
fi
exit 0
