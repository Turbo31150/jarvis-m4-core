#!/bin/bash
# Régulateur thermique PROPORTIONNEL M4 — flux constant, sans pic, "comme une mélodie".
# Module en continu max_perf_pct (% puissance CPU) pour tenir une température CIBLE.
# Aucune coupure brutale de services : on lisse la puissance, on n'arrête rien.
trap '' USR1 SIGUSR1
LOG=/tmp/m4-thermal-governor.log
PCT=/sys/devices/system/cpu/intel_pstate/max_perf_pct
CIBLE=82      # °C visés en régime permanent
CRIT=94       # °C : repli fort (jamais de kill, juste forte réduction)
MIN=45        # plancher de puissance (reste réactif)
MAX=100       # plafond
STEP=3        # pas de modulation (fin = lissage doux)
cur=100
echo "$(date '+%F %T') GOVERNOR START cible=${CIBLE}C" >> "$LOG"
while true; do
  T=$(cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | sort -n | tail -1); T=$((T/1000))
  if   [ "$T" -ge "$CRIT" ];          then cur=$MIN
  elif [ "$T" -ge $((CIBLE+5)) ];     then cur=$((cur-STEP*2))   # nettement au-dessus -> baisse +
  elif [ "$T" -ge "$CIBLE" ];         then cur=$((cur-STEP))     # au-dessus -> baisse douce
  elif [ "$T" -le $((CIBLE-8)) ];     then cur=$((cur+STEP))     # bien en-dessous -> remonte
  fi                                                              # zone morte [74-82] = on tient
  [ "$cur" -gt "$MAX" ] && cur=$MAX
  [ "$cur" -lt "$MIN" ] && cur=$MIN
  echo "$cur" | sudo -n tee "$PCT" >/dev/null 2>&1
  echo "$(date '+%F %T') T=${T}C -> max_perf=${cur}%" >> "$LOG"
  sleep 5
done
