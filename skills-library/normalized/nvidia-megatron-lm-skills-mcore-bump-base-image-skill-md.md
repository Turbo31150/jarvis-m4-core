---
id: nvidia-megatron-lm-skills-mcore-bump-base-image-skill-md
name: "mcore-bump-base-image"
author: "NVIDIA"
repository: "https://github.com/NVIDIA/Megatron-LM/tree/main/skills/mcore-bump-base-image"
skill_url: "https://skillsmp.com/creators/nvidia/megatron-lm/skills-mcore-bump-base-image"
stars: 17319
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:30:15.178816"
---

# Résumé
Bump the NVIDIA PyTorch base image (`nvcr.io/nvidia/pytorch:YY.MM-py3`) used by Megatron-LM CI. Covers the two pin sites (GitHub CI in `docker/.ngc_version.dev` and GitLab CI in `.gitlab/stages/01.build.yml`), the post-bump CI loop (re-run functional tests, refresh golden values, mark broken tests), and the gotchas that bit PRs

# Objectif
Skill d'automatisation/intégration pour mcore-bump-base-image.

# Déclencheurs d’utilisation
Mots-clés associés: mcore-bump-base-image, NVIDIA

# Procédure
Consulter le dépôt source: https://github.com/NVIDIA/Megatron-LM/tree/main/skills/mcore-bump-base-image

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
