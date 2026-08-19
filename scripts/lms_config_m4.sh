#!/bin/bash
# ================================================
# CONFIG LM Studio M4 — RTX 3050 Laptop 4Go
# Optimisation VRAM 4Go + benchmark massif
# ================================================

export PATH="$HOME/.lmstudio/bin:$PATH"
LMS="$HOME/.lmstudio/bin/lms"

echo "🔧 Configuration LM Studio M4 — RTX 3050 4Go"
echo "=============================================="

# Modèles recommandés pour 4Go VRAM (entrent entièrement en GPU)
MODELS_4GO=(
  "bartowski/Qwen2.5-Coder-1.5B-Instruct-GGUF/Qwen2.5-Coder-1.5B-Instruct-Q8_0.gguf"
  "bartowski/Qwen2.5-Coder-3B-Instruct-GGUF/Qwen2.5-Coder-3B-Instruct-Q6_K.gguf"  
  "bartowski/Phi-3.5-mini-instruct-GGUF/Phi-3.5-mini-instruct-Q4_K_M.gguf"
  "bartowski/Llama-3.2-3B-Instruct-GGUF/Llama-3.2-3B-Instruct-Q6_K.gguf"
  "bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF/DeepSeek-R1-Distill-Qwen-1.5B-Q8_0.gguf"
  "bartowski/gemma-3-1b-it-GGUF/gemma-3-1b-it-Q8_0.gguf"
)

echo ""
echo "📥 Téléchargement modèles adaptés RTX 3050 4Go..."
for MODEL in "${MODELS_4GO[@]}"; do
  echo "  → $MODEL"
  $LMS get "$MODEL" --yes 2>/dev/null || echo "    ⚠️ Déjà présent ou erreur"
done

echo ""
echo "✅ Modèles prêts. Lancement benchmark..."
bash ~/jarvis/scripts/lms_benchmark_m4.sh
