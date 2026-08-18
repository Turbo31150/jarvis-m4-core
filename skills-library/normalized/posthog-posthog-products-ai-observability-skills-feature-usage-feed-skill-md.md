---
{
  "name": "feature-usage-feed",
  "source": "https://skillsmp.com/creators/posthog/posthog/products-ai-observability-skills-feature-usage-feed",
  "repository": "https://github.com/PostHog/posthog/tree/master/products/ai_observability/skills/feature-usage-feed",
  "author": "PostHog",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:28:11+00:00",
  "verified": false,
  "quality_score": 89,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "879ea8c7bd210b0e1adf219ee3b5ef706fa2b1584d0d34c7b03a5531662b36d2"
}
---

# Résumé
Set up an LLM-judge evaluation that extracts canonical use cases for a PostHog feature at scale and streams the results to a Slack channel as a live feed. Use when someone wants to understand how users are actually using a specific AI/LLM-powered feature in production — what they're investigating, what questions they're trying to answer, and what patterns surface — without manually reading hundreds of traces. Assumes the feature emits `$ai_generation` and `$ai_evaluation` events with `$session_id` linkage to the trigger user's recording (the standard setup post the session-summary linkage PRs).

# Source originale
- SkillsMP : https://skillsmp.com/creators/posthog/posthog/products-ai-observability-skills-feature-usage-feed
- Dépôt    : https://github.com/PostHog/posthog/tree/master/products/ai_observability/skills/feature-usage-feed

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
