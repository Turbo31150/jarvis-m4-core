---
{
  "name": "pre-publish-review",
  "source": "https://skillsmp.com/creators/code-yeongyu/oh-my-openagent/agents-skills-pre-publish-review",
  "repository": "https://github.com/code-yeongyu/oh-my-openagent/tree/dev/.agents/skills/pre-publish-review",
  "author": "code-yeongyu",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:30:47+00:00",
  "verified": false,
  "quality_score": 95,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "75b70fd7d69bff46616dbd0e7066b4daa12964254007f3ca0f4ac33dd7cf4c14"
}
---

# Résumé
Nuclear-grade 16-agent pre-publish release gate. Runs /get-unpublished-changes to detect all changes since last npm release, spawns up to 10 ultrabrain agents for deep per-change analysis, invokes /review-work (5 agents) for holistic review, and 1 oracle for overall release synthesis. Runs ONLY when the user explicitly asks for a pre-publish review — a plain publish/release request MUST NOT trigger this; /publish ships directly. Triggers: 'pre-publish review', 'review before publish', 'release review', 'pre-release review', 'ready to publish?', 'can I publish?', 'pre-publish', 'safe to publish', 'publishing review', 'pre-publish check'.

# Source originale
- SkillsMP : https://skillsmp.com/creators/code-yeongyu/oh-my-openagent/agents-skills-pre-publish-review
- Dépôt    : https://github.com/code-yeongyu/oh-my-openagent/tree/dev/.agents/skills/pre-publish-review

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
