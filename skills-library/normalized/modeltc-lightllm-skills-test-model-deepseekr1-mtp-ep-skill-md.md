---
id: modeltc-lightllm-skills-test-model-deepseekr1-mtp-ep-skill-md
name: "test-model-deepseekr1-mtp-ep"
author: "ModelTC"
repository: "https://github.com/ModelTC/LightLLM/tree/main/skills/test_model/deepseekr1-mtp-ep"
skill_url: "https://skillsmp.com/creators/modeltc/lightllm/skills-test-model-deepseekr1-mtp-ep"
stars: 4207
verified: false
quality_score: 100
security_score: 20
status: "DANGEROUS"
collected_at: "2026-08-07T17:30:15.180242"
---

# Résumé
Runs LightLLM DeepSeek-R1 EP MoE + MTP (EAGLE) server variants and GSM8K lm_eval against localhost. Requires each full run to use a dedicated log directory: persist every api_server process log under that tree (per-variant subdirectories recommended), write the consolidated summary to summary.txt in that same log directory, and keep artifacts separated from other test runs. Use when running DeepSeek-R1 MTP EP accuracy workflows or when the user asks to run these four server configurations one-by-one with logged results.

# Objectif
Skill d'automatisation/intégration pour test-model-deepseekr1-mtp-ep.

# Déclencheurs d’utilisation
Mots-clés associés: test-model-deepseekr1-mtp-ep, ModelTC

# Procédure
Consulter le dépôt source: https://github.com/ModelTC/LightLLM/tree/main/skills/test_model/deepseekr1-mtp-ep

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
