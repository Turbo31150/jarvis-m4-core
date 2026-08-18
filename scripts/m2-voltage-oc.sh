#!/bin/bash
# Quadro RTX 4000 x3 — OC serveur ML M2 : CUDA 12.6, fan adaptatif, clocks optimisés
export DISPLAY=:0
export CUDA_HOME=/usr/local/cuda-12.6
export LD_LIBRARY_PATH=/usr/local/cuda-12.6/lib64:$LD_LIBRARY_PATH

echo "[GPU-OC] M2 — configuration serveur ML..."

# Power limits max + persistence
for i in 0 1 2; do
    sudo nvidia-smi -pl 125 -i $i 2>/dev/null
done
nvidia-smi -pm 1 2>/dev/null

for i in 0 1 2; do
    TEMP=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader -i $i 2>/dev/null)
    # Fan adaptatif (°C → %)
    if [ "$TEMP" -ge 75 ]; then FAN=90
    elif [ "$TEMP" -ge 65 ]; then FAN=80
    else FAN=70; fi

    nvidia-settings -a "[gpu:$i]/GPUFanControlState=1" 2>/dev/null
    nvidia-settings -a "[fan:$i]/GPUTargetFanSpeed=$FAN" 2>/dev/null
    nvidia-settings -a "[gpu:$i]/GPUGraphicsClockOffset[3]=100" 2>/dev/null
    nvidia-settings -a "[gpu:$i]/GPUMemoryTransferRateOffset[3]=200" 2>/dev/null

    echo "[GPU-OC] GPU$i: core+100 mem+200 | fan=${FAN}% | temp=${TEMP}°C"
done
echo "[GPU-OC] M2 configuré — CUDA 12.6 actif"
