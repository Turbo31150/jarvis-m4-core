---
id: modeltc-lightllm-skills-test-model-qwen3-5-0-8b-pd-nixl-skill-md
name: "test-model-qwen3-5-0-8b-pd-nixl"
author: "ModelTC"
repository: "https://github.com/ModelTC/LightLLM/tree/main/skills/test_model/qwen3.5-0.8b-pd-nixl"
skill_url: "https://skillsmp.com/creators/modeltc/lightllm/skills-test-model-qwen3-5-0-8b-pd-nixl"
stars: 4207
verified: false
quality_score: 100
security_score: 20
status: "DANGEROUS"
collected_at: "2026-08-07T17:30:15.182462"
---

# Résumé
LightLLM Qwen3.5-0.8B PD disaggregation over NIXL gsm8k: pd_master on 8089, prefill on 8001, decode on 8002. Supports TP1 and TP2 runs by setting TP / PREFILL_CUDA_DEVICES / DECODE_CUDA_DEVICES. Qwen3.5 has linear-attention state transfer; use --pd_kv_page_size 2048 and --pd_kv_page_num 16. lm_eval hits pd_master URL. Requires UCX/RDMA env, nvidia_peermem check, curl warmup before lm_eval, registration wait in pd_master.log, and summary.txt. Includes optional repeated-prompt decode cache probe for linear-att page-boundary behavior.

# Objectif
Skill d'automatisation/intégration pour test-model-qwen3-5-0-8b-pd-nixl.

# Déclencheurs d’utilisation
Mots-clés associés: test-model-qwen3-5-0-8b-pd-nixl, ModelTC

# Procédure
Consulter le dépôt source: https://github.com/ModelTC/LightLLM/tree/main/skills/test_model/qwen3.5-0.8b-pd-nixl

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
