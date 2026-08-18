---
id: posthog-posthog-agents-skills-writing-evals-skill-md
name: "writing-evals"
author: "PostHog"
repository: "https://github.com/PostHog/posthog/tree/master/.agents/skills/writing-evals"
skill_url: "https://skillsmp.com/creators/posthog/posthog/agents-skills-writing-evals"
stars: 37496
verified: false
quality_score: 100
security_score: 20
status: "DANGEROUS"
collected_at: "2026-08-07T17:08:31.693332"
---

# Résumé
Teaches how to write and run evals on the `products/posthog_ai/eval_harness/` harness — sandboxed agent suites that execute the real coding agent in a Docker or Modal sandbox against a seeded Hedgebox project, and one-shot suites that score a single in-process model invocation per case. Use when adding or changing eval suites, cases, scorers, seeders, or synthesizers under `products/posthog_ai/evals/` or `products/*/evals/`, when touching the harness under `products/posthog_ai/eval_harness/`, or when running or debugging those evals (`hogli evals`). Covers suite kinds and discovery, case anatomy, the seeder/synthesizer split, the one-branch scorer patterns, and how to read results. Not for `ee/hogai/eval/ci/` pytest evals, and not for the LLM Analytics product's evaluation features.

# Objectif
Skill d'automatisation/intégration pour writing-evals.

# Déclencheurs d’utilisation
Mots-clés associés: writing-evals, PostHog

# Procédure
Consulter le dépôt source: https://github.com/PostHog/posthog/tree/master/.agents/skills/writing-evals

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
