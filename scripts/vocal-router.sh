#!/bin/bash
# JARVIS Vocal Router — failover M1→M2→M3→M4
# Trouve le premier nœud whisper disponible

NODES=("127.0.0.1:18001" "127.0.0.1:18001" "127.0.0.1:18001" "127.0.0.1:18800")
LABELS=("M1-RTX3080" "M2-Quadro4000" "M3-GTX1660S" "M4-Windows")

for i in "${!NODES[@]}"; do
  if curl -sf --max-time 2 "http://${NODES[$i]}/" > /dev/null 2>&1; then
    echo "${LABELS[$i]} ${NODES[$i]}"
    exit 0
  fi
done
echo "NONE — aucun nœud whisper disponible"
exit 1
