---
id: posthog-posthog-products-experiments-skills-diagnosing-experiment-results-skill-md
name: "diagnosing-experiment-results"
author: "PostHog"
repository: "https://github.com/PostHog/posthog/tree/master/products/experiments/skills/diagnosing-experiment-results"
skill_url: "https://skillsmp.com/creators/posthog/posthog/products-experiments-skills-diagnosing-experiment-results"
stars: 37496
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:09:04.185563"
---

# Résumé
Diagnoses bias, anomalies, and strange-looking results on a specific PostHog experiment. Covers empty / 0-exposure experiments, sample ratio mismatch, identity fragmentation, multi-variant exposure, uneven-split exclusion bias, significance traps (peeking, A/A, Bayesian vs Frequentist), PostHog-vs-SQL discrepancies, and surprises after mid-run edits. Symptom-driven dispatch to the right diagnostic.
TRIGGER when: user asks 'is my experiment biased?' or 'why 0 exposures?', references the bias banner, says a variant looks strange / wrong / off, sees significance flipping, notices PostHog numbers disagreeing with their SQL, sees an A/A test showing significance, or reports surprises after mid-run edits.
DO NOT TRIGGER when: creating a new experiment (use creating-experiments), only configuring rollout (use configuring-experiment-rollout) or metrics (use configuring-experiment-analytics), or only asking lifecycle questions (use managing-experiment-lifecycle).

# Objectif
Skill d'automatisation/intégration pour diagnosing-experiment-results.

# Déclencheurs d’utilisation
Mots-clés associés: diagnosing-experiment-results, PostHog

# Procédure
Consulter le dépôt source: https://github.com/PostHog/posthog/tree/master/products/experiments/skills/diagnosing-experiment-results

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
