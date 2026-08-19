#!/bin/bash
# ==============================================================================
# JARVIS-OMEGA — Hyper-Cluster Multi-Shell Locomotive (Pleine Puissance)
# ==============================================================================
set -e

echo "🚀 [HYPER-CLUSTER] Activation de la puissance maximale du cluster JARVIS..."

# 1. Salve de génération et d'inférence massive
python3 /home/pamerys/jarvis/scripts/jarvis_omega_10k_orchestrator.py --once &
PID_10K=$!

# 2. Salve de production documentaire & Devis B2B
python3 /home/pamerys/jarvis/scripts/jarvis_massive_executor.py &
PID_DOCS=$!

# 3. Salve de visibilité et diffusion BrowserOS
python3 /home/pamerys/jarvis/scripts/jarvis_growth_algorithm_booster.py &
PID_SOC=$!

# 4. Salve de prospection OpenClaw
python3 /home/pamerys/jarvis-cowork/scripts/openclaw_massive_prospection.py &
PID_CLAW=$!

# 5. Salve d'inférence locale Ollama / LMStudio (Test de charge)
bash /home/pamerys/jarvis/scripts/ask-local.sh "Résume en 2 phrases techniques les avantages d'un cluster d'inférence On-Premise sous NIS2." > /tmp/llm_test_out.txt 2>&1 &
PID_LLM=$!

echo "⏳ Attente de synchronisation des 5 travailleurs parallèles..."
wait $PID_10K $PID_DOCS $PID_SOC $PID_CLAW $PID_LLM || true

# Nettoyage Zéro-Déchet
rm -f /tmp/*.png /tmp/*.xml /tmp/*.3gp /tmp/*.wav /tmp/*.mp3 /tmp/llm_test_out.txt 2>/dev/null

echo "✅ [HYPER-CLUSTER] Salve multi-shell pleine puissance achevée !"
