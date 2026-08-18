---
id: posthog-posthog-products-posthog-ai-skills-checking-deploy-timing-skill-md
name: "checking-deploy-timing"
author: "PostHog"
repository: "https://github.com/PostHog/posthog/tree/master/products/posthog_ai/skills/checking-deploy-timing"
skill_url: "https://skillsmp.com/creators/posthog/posthog/products-posthog-ai-skills-checking-deploy-timing"
stars: 37496
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:30:23.404372"
---

# Résumé
Determine when a PostHog code change reached a given environment by reading the hidden GIT deploy annotations in the project and correlating them with the merge commit on GitHub. Use when PostHog staff ask "when was X deployed", "is my change live in the US/EU yet", "has my PR shipped", "did the fix roll out to prod-us", or otherwise want to know whether/when a commit, PR, or feature went out to a region. Do not answer deploy-timing questions from event/data volume alone — that only shows when data changed, not when code shipped.

# Objectif
Skill d'automatisation/intégration pour checking-deploy-timing.

# Déclencheurs d’utilisation
Mots-clés associés: checking-deploy-timing, PostHog

# Procédure
Consulter le dépôt source: https://github.com/PostHog/posthog/tree/master/products/posthog_ai/skills/checking-deploy-timing

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
