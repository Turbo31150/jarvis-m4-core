---
id: posthog-posthog-agents-skills-analyzing-experiment-query-performance-skill-md
name: "analyzing-experiment-query-performance"
author: "PostHog"
repository: "https://github.com/PostHog/posthog/tree/master/.agents/skills/analyzing-experiment-query-performance"
skill_url: "https://skillsmp.com/creators/posthog/posthog/agents-skills-analyzing-experiment-query-performance"
stars: 37496
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:30:23.404204"
---

# Résumé
Pull and interpret production experiment query-performance data from the staff-only `/api/debug_ch_queries` endpoints backing the `/instance/query_performance` scene: slowest experiment queries, precompute read/build health, and preaggregation cache footprint. Covers prod-US and prod-EU via a `query_performance:read` personal API key, all query params, and response field semantics (exception codes, exposure paths, precompute skip reasons, job states). Use when investigating slow or failing experiment queries, precompute regressions, 307/159/241 errors, preaggregation table growth, or when asked how experiment query performance or the precompute rollout is doing in production.

# Objectif
Skill d'automatisation/intégration pour analyzing-experiment-query-performance.

# Déclencheurs d’utilisation
Mots-clés associés: analyzing-experiment-query-performance, PostHog

# Procédure
Consulter le dépôt source: https://github.com/PostHog/posthog/tree/master/.agents/skills/analyzing-experiment-query-performance

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
