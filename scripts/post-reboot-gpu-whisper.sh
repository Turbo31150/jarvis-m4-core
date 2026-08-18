#!/usr/bin/env bash
# À exécuter APRÈS reboot : finalise migration Whisper sur GPU
set -euo pipefail
LOG=/tmp/post-reboot-gpu.log
exec > >(tee -a "$LOG") 2>&1

echo "=========================================="
echo "JARVIS — Post-Reboot GPU Whisper migration"
echo "=========================================="

echo ""
echo "[1/6] Vérif driver NVIDIA"
if ! command -v nvidia-smi >/dev/null || ! nvidia-smi &>/dev/null; then
  echo "❌ Aucun GPU NVIDIA compatible détecté ou pilotes inactifs. Migration GPU impossible."
  exit 1
fi
nvidia-smi --query-gpu=index,name,memory.total,driver_version --format=csv
echo ""

echo "[2/6] Vérif CUDA toolkit"
nvcc --version 2>&1 | head -4 || echo "nvcc absent (OK si on n'utilise que les libs runtime)"
echo ""

echo "[3/6] Install libs CUDA cuDNN/cuBLAS pour faster-whisper"
pip install --user --quiet --upgrade nvidia-cublas-cu12 nvidia-cudnn-cu12==9.* ctranslate2 faster-whisper 2>&1 | tail -5
echo ""

echo "[4/6] Test faster-whisper CUDA"
python3 -c "
from faster_whisper import WhisperModel
import sys
print('Chargement distil-large-v3 sur cuda…')
m = WhisperModel('distil-large-v3', device='cuda', compute_type='float16')
print('Modèle chargé OK ✓')
" 2>&1 | tail -10
echo ""

echo "[5/6] Bascule whisper API → version GPU"
sudo systemctl stop jarvis-whisper-api 2>&1 || true
sudo cp /home/pamerys/IA/Core/jarvis/core/jarvis_whisper_api.py /home/pamerys/IA/Core/jarvis/core/jarvis_whisper_api.cpu.bak.py
sudo cp /home/pamerys/IA/Core/jarvis/core/jarvis_whisper_api.gpu.py /home/pamerys/IA/Core/jarvis/core/jarvis_whisper_api.py
echo "✓ jarvis_whisper_api.py swappé (backup .cpu.bak.py)"

echo ""
echo "[6/6] Restart service"
sudo systemctl restart jarvis-whisper-api
sleep 6
echo "--- Status ---"
systemctl status jarvis-whisper-api --no-pager | head -15
echo ""
echo "--- Health ---"
curl -sS http://127.0.0.1:9743/health
echo ""
echo ""
echo "✅ Migration terminée. Teste Alt+X."
echo "Log complet : $LOG"
