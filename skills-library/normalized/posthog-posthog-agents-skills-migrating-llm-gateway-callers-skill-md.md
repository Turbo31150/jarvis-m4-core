---
{
  "name": "migrating-llm-gateway-callers",
  "source": "https://skillsmp.com/creators/posthog/posthog/agents-skills-migrating-llm-gateway-callers",
  "repository": "https://github.com/PostHog/posthog/tree/master/.agents/skills/migrating-llm-gateway-callers",
  "author": "PostHog",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:28:11+00:00",
  "verified": false,
  "quality_score": 95,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "2b59c56c6c3b312bfac4d8cea181534581ff2fdc6f70a93d8c40f479e4a11367"
}
---

# Résumé
Migrates an LLM caller from services/llm-gateway to PostHog/ai-gateway. Use when adding a gateway caller, converting an existing Python gateway integration, adopting shared Go-capable client builders, changing gateway URLs or headers for a caller, or removing a Python fallback. Inventories the caller's contract, checks the parity record, implements the supported migration, updates tests, and stops with a documented blocker when Go parity is missing.

# Source originale
- SkillsMP : https://skillsmp.com/creators/posthog/posthog/agents-skills-migrating-llm-gateway-callers
- Dépôt    : https://github.com/PostHog/posthog/tree/master/.agents/skills/migrating-llm-gateway-callers

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
