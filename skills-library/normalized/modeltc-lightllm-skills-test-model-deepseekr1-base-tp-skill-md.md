---
id: modeltc-lightllm-skills-test-model-deepseekr1-base-tp-skill-md
name: "test-model-deepseekr1-base-tp"
author: "ModelTC"
repository: "https://github.com/ModelTC/LightLLM/tree/main/skills/test_model/deepseekr1-base-tp"
skill_url: "https://skillsmp.com/creators/modeltc/lightllm/skills-test-model-deepseekr1-base-tp"
stars: 4207
verified: false
quality_score: 100
security_score: 20
status: "DANGEROUS"
collected_at: "2026-08-07T17:30:15.181143"
---

# Résumé
Runs LightLLM DeepSeek-R1 baseline TP gsm8k: single api_server with --tp 8 and --batch_max_tokens only, no MTP draft, no --dp, no EP MoE (distinct from deepseekr1-mtp-tp which adds MTP). GSM8K lm_eval on localhost port 8089. Requires a dedicated log directory, api_server and eval logs under that tree, summary.txt as consolidated report, tokenizer aligned with MODEL_DIR. Use for baseline R1 tensor-parallel accuracy runs without MTP/EP.

# Objectif
Skill d'automatisation/intégration pour test-model-deepseekr1-base-tp.

# Déclencheurs d’utilisation
Mots-clés associés: test-model-deepseekr1-base-tp, ModelTC

# Procédure
Consulter le dépôt source: https://github.com/ModelTC/LightLLM/tree/main/skills/test_model/deepseekr1-base-tp

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
