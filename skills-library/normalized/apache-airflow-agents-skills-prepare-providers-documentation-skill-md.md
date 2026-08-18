---
{
  "name": "prepare-providers-documentation",
  "source": "https://skillsmp.com/creators/apache/airflow/agents-skills-prepare-providers-documentation",
  "repository": "https://github.com/apache/airflow/tree/main/.agents/skills/prepare-providers-documentation",
  "author": "apache",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:28:07+00:00",
  "verified": false,
  "quality_score": 95,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "409c298e4da26989c7549847e25f126ed7c1de712b5b36dc3bba1147105602b8"
}
---

# Résumé
Replace the manual commit-by-commit classification step in `breeze release-management prepare-provider-documentation` with AI-driven classification. For each provider with pending changes, analyze every PR (batched into one sub-agent per provider, not one per PR), pay special attention to potentially breaking changes by inspecting the actual diff, scope multi-provider PRs to the current provider's slice, ask the release manager when uncertain, and apply version bumps + changelog entries. Use during the regular provider release cycle as an alternative to the interactive breeze prompts.

# Source originale
- SkillsMP : https://skillsmp.com/creators/apache/airflow/agents-skills-prepare-providers-documentation
- Dépôt    : https://github.com/apache/airflow/tree/main/.agents/skills/prepare-providers-documentation

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
