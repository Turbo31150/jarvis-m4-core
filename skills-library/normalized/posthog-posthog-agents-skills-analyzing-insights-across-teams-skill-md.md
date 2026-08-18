---
id: posthog-posthog-agents-skills-analyzing-insights-across-teams-skill-md
name: "analyzing-insights-across-teams"
author: "PostHog"
repository: "https://github.com/PostHog/posthog/tree/master/.agents/skills/analyzing-insights-across-teams"
skill_url: "https://skillsmp.com/creators/posthog/posthog/agents-skills-analyzing-insights-across-teams"
stars: 37496
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:09:07.592591"
---

# Résumé
Analyze PostHog insights, dashboards, or teams beyond the current project by querying the prod Postgres replicas synced into the dogfood data warehouse (US project 2, "PostHog App + Website"). Use when asked to analyze insights across all teams or projects, another team's insights, or fleet-wide insight/dashboard usage — cases where `system.insights` only returns the current project's rows and the agent would otherwise report the data as inaccessible. Covers the synced table names for US and EU and the column-verification workflow.

# Objectif
Skill d'automatisation/intégration pour analyzing-insights-across-teams.

# Déclencheurs d’utilisation
Mots-clés associés: analyzing-insights-across-teams, PostHog

# Procédure
Consulter le dépôt source: https://github.com/PostHog/posthog/tree/master/.agents/skills/analyzing-insights-across-teams

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
