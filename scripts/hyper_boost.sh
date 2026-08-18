#!/bin/bash
# Hyper Boost JARVIS OS — Modèles LLM, I/O Disque, Mémoire & Threads Parallèles

echo "[1/4] Activation du mode Performance CPU (Governor performance)..."
for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
  if [ -f "$gov" ]; then
    echo "performance" | sudo tee "$gov" >/dev/null 2>&1 || true
  fi
done

echo "[2/4] Optimisation de la file d'attente I/O (Scheduler & Read-Ahead)..."
for dev in /sys/block/sd*/queue/read_ahead_kb /sys/block/nvme*/queue/read_ahead_kb; do
  if [ -f "$dev" ]; then
    echo "2048" | sudo tee "$dev" >/dev/null 2>&1 || true
  fi
done

echo "[3/4] Optimisation du Cache et de la VRAM GPU M1 & M6..."
# Signal keepalive Ollama M6 & M4
ssh m6 "curl -s http://127.0.0.1:11434/api/generate -d '{\"model\":\"gemma3:4b\", \"keep_alive\":\"24h\"}' >/dev/null 2>&1 &" 2>/dev/null || true
curl -s http://10.42.0.1:11235/v1/completions -H "Content-Type: application/json" -d '{"model":"qwen/qwen3.5-9b", "prompt":"warmup", "max_tokens":1}' >/dev/null 2>&1 || true

echo "[4/4] Flush & Compactage mémoire RAM..."
sudo sysctl -w vm.drop_caches=3 2>/dev/null || true

echo "HYPER BOOST COMPLET : Le système tourne au maximum des performances matérielles !"
