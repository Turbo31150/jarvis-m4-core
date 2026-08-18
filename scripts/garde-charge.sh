#!/usr/bin/env bash
# Garde de charge partagée — à brancher en ExecCondition d'un timer systemd.
# Sort 1 (condition non remplie, PAS un échec) quand la machine est déjà saturée :
# un timer qui déclenche sous famine empile des runs au lieu d'avancer.
#
#   Usage : garde-charge.sh [facteur_load] [ram_libre_mini_Mo]
#   Défaut : load1 > 1.5 × nproc  OU  moins de 2 Go dispo  → on saute le tick.
set -u

FACTEUR="${1:-1.5}"
RAM_MINI_MO="${2:-2048}"

COEURS=$(nproc 2>/dev/null || echo 4)
LOAD1=$(awk '{print $1}' /proc/loadavg)
# LC_ALL=C obligatoire : en locale FR, printf "%.2f" rend « 24,00 » (virgule).
# awk ne reconnaît pas ce littéral comme un nombre, bascule alors en comparaison
# de CHAÎNES, et « 8.16 » > « 24,00 » devient VRAI ('8' > '2' en lexicographique).
# Résultat observé le 2026-08-06 : « load 8.16 > 24,00 → tick sauté » — la garde
# refusait tous les ticks alors que la machine était largement disponible.
SEUIL=$(LC_ALL=C awk -v c="$COEURS" -v f="$FACTEUR" 'BEGIN{printf "%.2f", c*f}')
RAM_DISPO=$(awk '/MemAvailable/{printf "%d", $2/1024}' /proc/meminfo)

# +0 force le contexte numérique des deux côtés : ceinture et bretelles si un
# jour l'un des opérandes arrive dans un format inattendu.
if LC_ALL=C awk -v l="$LOAD1" -v s="$SEUIL" 'BEGIN{exit !(l+0 > s+0)}'; then
  echo "garde-charge: load $LOAD1 > $SEUIL ($COEURS cœurs) → tick sauté"
  exit 1
fi
if [ "${RAM_DISPO:-0}" -lt "$RAM_MINI_MO" ]; then
  echo "garde-charge: RAM dispo ${RAM_DISPO}Mo < ${RAM_MINI_MO}Mo → tick sauté"
  exit 1
fi
exit 0
