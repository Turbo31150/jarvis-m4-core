---
id: modeltc-lightllm-skills-test-model-qwen3-8b-gsm8k-scenarios-skill-md
name: "test-model-qwen3-8b-gsm8k-scenarios"
author: "ModelTC"
repository: "https://github.com/ModelTC/LightLLM/tree/main/skills/test_model/qwen3-8b-gsm8k-scenarios"
skill_url: "https://skillsmp.com/creators/modeltc/lightllm/skills-test-model-qwen3-8b-gsm8k-scenarios"
stars: 4207
verified: false
quality_score: 100
security_score: 20
status: "DANGEROUS"
collected_at: "2026-08-07T17:30:15.182574"
---

# Résumé
LightLLM Qwen3-8B GSM8K multi-scenario regression: seven isolated api_server configs (baseline, fp8w8a8 quant, tpsp mix, tpsp with dp2 and dp prefill balance, cpu cache, int8kv on top of cpu cache, disk cache with LIGHTLLM_DISK_CACHE_PROMPT_LIMIT_LENGTH). Each scenario then lm_eval gsm8k batch 500. Scenarios 5–7 run lm_eval twice for cache hit. Per-scenario LOG_DIR, server.log, eval logs, summary.txt. Default MODEL_DIR /mtc/models/qwen3-8b; DISK_CACHE_DIR /mtc/test/tmp/ for scenario 7; ask user if paths invalid. Fixed HTTP port 8089 (not configurable). nvidia-smi GPUs, port listen not health, clear proxies and no_proxy.

# Objectif
Skill d'automatisation/intégration pour test-model-qwen3-8b-gsm8k-scenarios.

# Déclencheurs d’utilisation
Mots-clés associés: test-model-qwen3-8b-gsm8k-scenarios, ModelTC

# Procédure
Consulter le dépôt source: https://github.com/ModelTC/LightLLM/tree/main/skills/test_model/qwen3-8b-gsm8k-scenarios

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
