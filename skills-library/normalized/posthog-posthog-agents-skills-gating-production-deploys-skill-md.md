---
id: posthog-posthog-agents-skills-gating-production-deploys-skill-md
name: "gating-production-deploys"
author: "PostHog"
repository: "https://github.com/PostHog/posthog/tree/master/.agents/skills/gating-production-deploys"
skill_url: "https://skillsmp.com/creators/posthog/posthog/agents-skills-gating-production-deploys"
stars: 37496
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:08:31.693238"
---

# Résumé
Use when adding or editing a GitHub Actions workflow that pushes a container image to a registry (ECR/ghcr/Docker Hub via build-push-action) or dispatches a production deploy (a `commit_state_update` repository_dispatch to PostHog/charts). Those run from a single canonical deploy repo, gated by the CD_DEPLOY_ENABLED variable. Does NOT apply to workflows that publish GitHub releases, npm, crates, or Homebrew — those stay on the public repo.

# Objectif
Skill d'automatisation/intégration pour gating-production-deploys.

# Déclencheurs d’utilisation
Mots-clés associés: gating-production-deploys, PostHog

# Procédure
Consulter le dépôt source: https://github.com/PostHog/posthog/tree/master/.agents/skills/gating-production-deploys

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
