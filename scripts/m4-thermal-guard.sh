#!/bin/bash
# Coupe-circuit thermique M4 — re-coupe la boucle DOMINO/OC dès le seuil critique.
# Réconcilie "tout relancer" avec "aucun blocage 100°C". Réversible: tuer le PID.
LOG=/tmp/m4-thermal-guard.log
SEUIL=93      # °C : coupure
RELACHE=78    # °C : on considère sain en dessous
echo "$(date '+%F %T') guard START seuil=${SEUIL}C" >> "$LOG"
while true; do
  T=$(cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | sort -n | tail -1)
  T=$((T/1000))
  if [ "$T" -ge "$SEUIL" ]; then
    echo "$(date '+%F %T') CUTOFF temp=${T}C -> coupe boucle + bridage" >> "$LOG"
    systemctl --user stop jarvis-domino.service jarvis-thermal-agent.service jarvis-cowork-loop.service 2>/dev/null
    pkill -9 -x llama-server 2>/dev/null
    pkill -9 -f lm-ask.sh 2>/dev/null
    echo 1 | sudo -n tee /sys/devices/system/cpu/intel_pstate/no_turbo >/dev/null 2>&1
    for g in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo powersave | sudo -n tee "$g" >/dev/null 2>&1; done
  fi
  sleep 10
done
