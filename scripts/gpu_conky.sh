#!/bin/bash
MODE="${1:-full}"
if ! command -v nvidia-smi &>/dev/null; then echo "  Aucun GPU NVIDIA"; exit 0; fi
case "$MODE" in
    thermal) nvidia-smi --query-gpu=index,temperature.gpu --format=csv,noheader | while IFS=, read -r idx temp; do printf "  GPU%s: %s°C\n" "$idx" "${temp// /}"; done ;;
    vram) nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv,noheader | while IFS=, read -r idx used total; do printf "  GPU%s: %s / %s\n" "$idx" "${used// /}" "${total// /}"; done ;;
    *) nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv,noheader | while IFS=, read -r idx name temp util used total; do printf "  GPU%s [%s]\n    Temp:%s°C  Util:%s%%  VRAM:%s/%s\n" "$idx" "${name// /}" "${temp// /}" "${util// /}" "${used// /}" "${total// /}"; done ;;
esac
