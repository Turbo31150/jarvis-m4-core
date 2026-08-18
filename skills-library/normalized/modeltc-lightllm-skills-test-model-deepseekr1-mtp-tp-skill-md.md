---
id: modeltc-lightllm-skills-test-model-deepseekr1-mtp-tp-skill-md
name: "test-model-deepseekr1-mtp-tp"
author: "ModelTC"
repository: "https://github.com/ModelTC/LightLLM/tree/main/skills/test_model/deepseekr1-mtp-tp"
skill_url: "https://skillsmp.com/creators/modeltc/lightllm/skills-test-model-deepseekr1-mtp-tp"
stars: 4207
verified: false
quality_score: 100
security_score: 20
status: "DANGEROUS"
collected_at: "2026-08-07T17:30:15.181274"
---

# Résumé
DeepSeek-R1 MTP-TP test: LightLLM api_server with MTP (EAGLE) draft, tensor parallel only (--tp 8, no --dp, no EP MoE), plus GSM8K lm_eval on localhost. Distinct from the MTP-EP-TPDP skill which uses --tp 8 --dp 8 and EP MoE. Requires a dedicated log directory, summary.txt, tokenizer aligned with MODEL_DIR. Use for TP-only MTP gsm8k accuracy runs.

# Objectif
Skill d'automatisation/intégration pour test-model-deepseekr1-mtp-tp.

# Déclencheurs d’utilisation
Mots-clés associés: test-model-deepseekr1-mtp-tp, ModelTC

# Procédure
Consulter le dépôt source: https://github.com/ModelTC/LightLLM/tree/main/skills/test_model/deepseekr1-mtp-tp

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
