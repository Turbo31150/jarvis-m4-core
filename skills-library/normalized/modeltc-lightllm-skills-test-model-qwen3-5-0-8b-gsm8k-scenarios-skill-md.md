---
id: modeltc-lightllm-skills-test-model-qwen3-5-0-8b-gsm8k-scenarios-skill-md
name: "test-model-qwen3-5-0-8b-gsm8k-scenarios"
author: "ModelTC"
repository: "https://github.com/ModelTC/LightLLM/tree/main/skills/test_model/qwen3.5-0.8b-gsm8k-scenarios"
skill_url: "https://skillsmp.com/creators/modeltc/lightllm/skills-test-model-qwen3-5-0-8b-gsm8k-scenarios"
stars: 4207
verified: false
quality_score: 100
security_score: 20
status: "DANGEROUS"
collected_at: "2026-08-07T17:30:15.182356"
---

# Résumé
LightLLM Qwen3.5-0.8B GSM8K multi-scenario regression: five isolated runs (baseline api_server, prefill cudagraph, linear-attention cache flags, CPU cache plus linear-att, disk cache with LIGHTLLM_DISK_CACHE_PROMPT_LIMIT_LENGTH). Each scenario uses api_server tp 2 port 8089, then lm_eval local-completions gsm8k batch 500. Scenarios 4 and 5 run lm_eval twice for cache warm hit. Per-scenario LOG_DIR, server.log, eval logs, summary.txt. GPUs from nvidia-smi; port listen readiness not health; clear proxies and set no_proxy. Default MODEL_DIR HuggingFace hub snapshot path; default DISK_CACHE_DIR /mtc/test/tmp/ for scenario 5; ask user for paths if missing or not writable.

# Objectif
Skill d'automatisation/intégration pour test-model-qwen3-5-0-8b-gsm8k-scenarios.

# Déclencheurs d’utilisation
Mots-clés associés: test-model-qwen3-5-0-8b-gsm8k-scenarios, ModelTC

# Procédure
Consulter le dépôt source: https://github.com/ModelTC/LightLLM/tree/main/skills/test_model/qwen3.5-0.8b-gsm8k-scenarios

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
