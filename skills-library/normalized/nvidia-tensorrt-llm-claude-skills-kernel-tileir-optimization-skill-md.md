---
id: nvidia-tensorrt-llm-claude-skills-kernel-tileir-optimization-skill-md
name: "kernel-tileir-optimization"
author: "NVIDIA"
repository: "https://github.com/NVIDIA/TensorRT-LLM/tree/main/.claude/skills/kernel-tileir-optimization"
skill_url: "https://skillsmp.com/creators/nvidia/tensorrt-llm/claude-skills-kernel-tileir-optimization"
stars: 14292
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:30:30.557205"
---

# Résumé
Optimize existing Triton kernels for NVIDIA TileIR backend on Blackwell GPUs (sm_100+). Adds TileIR-specific autotune configs: occupancy, num_ctas, TMA descriptors. Covers kernel classification (dot-related, norm-like, elementwise, reduction), type-specific transformations, and PTX-vs-TileIR benchmarking. Triggered by: "optimize for TileIR", "add TileIR configs", "Blackwell optimization", "TMA descriptors", "2CTA mode", "occupancy tuning". Kernels use standard `import triton`; TileIR activates via ENABLE_TILE=1 when nvtriton is installed.

# Objectif
Skill d'automatisation/intégration pour kernel-tileir-optimization.

# Déclencheurs d’utilisation
Mots-clés associés: kernel-tileir-optimization, NVIDIA

# Procédure
Consulter le dépôt source: https://github.com/NVIDIA/TensorRT-LLM/tree/main/.claude/skills/kernel-tileir-optimization

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
