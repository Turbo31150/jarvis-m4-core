---
id: modeltc-lightllm-skills-test-model-deepseekv32-ep-skill-md
name: "test-model-deepseekv32-ep"
author: "ModelTC"
repository: "https://github.com/ModelTC/LightLLM/tree/main/skills/test_model/deepseekv32-ep"
skill_url: "https://skillsmp.com/creators/modeltc/lightllm/skills-test-model-deepseekv32-ep"
stars: 4207
verified: false
quality_score: 100
security_score: 20
status: "DANGEROUS"
collected_at: "2026-08-07T17:30:15.182037"
---

# Résumé
Runs LightLLM DeepSeek-V3.2 EP MoE gsm8k: api_server with --tp 8 --dp 8 --enable_ep_moe, tool_call_parser deepseekv32, reasoning_parser deepseek-v3, graph_max_batch_size 32, mem_fraction 0.8, LOADWORKER 14, port 8000 aligned with lm_eval base_url. Requires a dedicated log directory, api_server and eval logs, summary.txt consolidated report. lm_eval uses tokenizer_backend=null (server-side tokenization) because local transformers does not recognize model_type deepseek_v32. Distinct from R1 MTP/Base flows. Use for V3.2 EP MoE gsm8k accuracy on LightLLM.

# Objectif
Skill d'automatisation/intégration pour test-model-deepseekv32-ep.

# Déclencheurs d’utilisation
Mots-clés associés: test-model-deepseekv32-ep, ModelTC

# Procédure
Consulter le dépôt source: https://github.com/ModelTC/LightLLM/tree/main/skills/test_model/deepseekv32-ep

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
