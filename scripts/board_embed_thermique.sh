#!/usr/bin/env bash
# Vectorise le board par tranches, en respectant la cible thermique du M4.
#
# Backend : Ollama local, nomic-embed-text, endpoint OpenAI-compatible.
# Mesuré 201 chunks/s en batch de 64 — contre 0,6 sur M6 LM Studio, qui
# refuse les lots > 16 (HTTP 400) et la concurrence (HTTP 500).
#
# En continu, ce débit pousse le SoC à 98 °C : la vitesse n'est donc pas le
# facteur limitant, la dissipation l'est. On découpe en tranches et on attend
# le refroidissement entre chacune — le débit moyen tombe mais la machine
# tient, et le commit incrémental de board.py rend chaque tranche acquise.
set -euo pipefail

CIBLE=${CIBLE:-78}       # on repart sous la cible de 82 °C, pas dessus
TRANCHE=${TRANCHE:-1000}
PAUSE=${PAUSE:-90}
cd /home/pamerys/jarvis/board

temp() { awk '{printf "%.0f", $1/1000}' /sys/class/thermal/thermal_zone6/temp; }

while :; do
  restants=$(sqlite3 "file:board.db?mode=ro" "select count(*) from chunks where embedding is null;")
  if [ "$restants" -eq 0 ]; then
    echo "✓ board entièrement vectorisé"
    break
  fi

  while [ "$(temp)" -ge "$CIBLE" ]; do
    echo "  ⏸ $(temp) °C ≥ ${CIBLE} °C — refroidissement ${PAUSE} s ($restants restants)"
    sleep "$PAUSE"
  done

  echo "▶ tranche de $TRANCHE — $restants restants — $(temp) °C"
  BOARD_LMS_URL=http://127.0.0.1:11434/v1 \
  BOARD_EMBED_MODEL=nomic-embed-text \
  BOARD_EMBED_LOT=64 BOARD_EMBED_PAR=1 \
    python3 board.py embed --limit "$TRANCHE" 2>&1 | tail -2

  sleep "$PAUSE"   # laisse le SoC redescendre avant la tranche suivante
done
