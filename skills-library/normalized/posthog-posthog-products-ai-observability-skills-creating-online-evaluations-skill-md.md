---
id: posthog-posthog-products-ai-observability-skills-creating-online-evaluations-skill-md
name: "creating-online-evaluations"
author: "PostHog"
repository: "https://github.com/PostHog/posthog/tree/master/products/ai_observability/skills/creating-online-evaluations"
skill_url: "https://skillsmp.com/creators/posthog/posthog/products-ai-observability-skills-creating-online-evaluations"
stars: 37496
verified: false
quality_score: 100
security_score: 20
status: "DANGEROUS"
collected_at: "2026-08-07T17:30:27.034721"
---

# Résumé
Author continuously-running online evaluations in PostHog AI observability, grounded in a real failure mode you've identified. Use when the user wants an evaluation that automatically scores new generations or whole traces going forward — "create an eval to catch X", "continuously check that responses do Y", "turn this failure into an eval". Covers choosing the target and eval type (hog / llm_judge / sentiment), configuring a provider, model, and usable provider key for an llm_judge eval, scoping which generations trigger it via conditions (property filters + rollout sampling), creating it disabled, verifying scope, and enabling. Finding and ranking the failure modes worth evaluating is its own job — use exploring-ai-failures first. To debug or manage evaluations that already exist, use exploring-llm-evaluations.

# Objectif
Skill d'automatisation/intégration pour creating-online-evaluations.

# Déclencheurs d’utilisation
Mots-clés associés: creating-online-evaluations, PostHog

# Procédure
Consulter le dépôt source: https://github.com/PostHog/posthog/tree/master/products/ai_observability/skills/creating-online-evaluations

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
