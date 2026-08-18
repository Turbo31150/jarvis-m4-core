---
{
  "name": "finding-llm-gateway-migration-candidates",
  "source": "https://skillsmp.com/creators/posthog/posthog/agents-skills-finding-llm-gateway-migration-candidates",
  "repository": "https://github.com/PostHog/posthog/tree/master/.agents/skills/finding-llm-gateway-migration-candidates",
  "author": "PostHog",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:28:11+00:00",
  "verified": false,
  "quality_score": 89,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "e641ff02d226bc47ca10fa90695241776a25bc074ff5f023e7d6005a5d933255"
}
---

# Résumé
Finds and ranks callers that could move from services/llm-gateway to PostHog/ai-gateway. Use when asked what to migrate next, to find low-risk gateway migration candidates, to audit remaining Python gateway callers, or to identify callers blocked by Go gateway parity. Searches code and deployment wiring, inventories each caller's required contract, filters out unsupported migrations, and returns an evidence-backed shortlist without changing callers.

# Source originale
- SkillsMP : https://skillsmp.com/creators/posthog/posthog/agents-skills-finding-llm-gateway-migration-candidates
- Dépôt    : https://github.com/PostHog/posthog/tree/master/.agents/skills/finding-llm-gateway-migration-candidates

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
