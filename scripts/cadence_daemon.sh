#!/bin/bash
# Daemon à très haute cadence : boucle toutes les 2 secondes
while true; do
  python3 /home/pamerys/jarvis/scripts/turbo_cadence_engine.py >/dev/null 2>&1
  sleep 2
done
