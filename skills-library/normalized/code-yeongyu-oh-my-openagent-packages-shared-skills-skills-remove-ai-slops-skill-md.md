---
{
  "name": "remove-ai-slops",
  "source": "https://skillsmp.com/creators/code-yeongyu/oh-my-openagent/packages-shared-skills-skills-remove-ai-slops",
  "repository": "https://github.com/code-yeongyu/oh-my-openagent/tree/dev/packages/shared-skills/skills/remove-ai-slops",
  "author": "code-yeongyu",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:28:03+00:00",
  "verified": false,
  "quality_score": 95,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "c69490b26a48963e686fc4d6bd515a89196fe2a7abe1a5dd74421553171d5bb3"
}
---

# Résumé
Remove AI-generated code smells (slop) from branch changes or an explicit file list. Locks behavior with regression tests FIRST, then runs categorized cleanup via parallel `deep` agents in batches of 5, then verifies with quality gates. Covers 10 slop categories including performance equivalences, excessive complexity (object annotations, if/elif variant chains), and oversized modules (250+ pure LOC with mandatory modular refactoring). MUST USE when the user asks to "remove slop", "clean AI code", "deslop", "clean up AI-generated code", "remove AI slop", or wants to clean up AI-generated patterns from recent changes. Triggers - "remove ai slops", "clean ai code", "deslop", "cleanup AI generated", "remove AI slop", "clean up AI-generated code", "strip slop", "ai-slop cleanup".

# Source originale
- SkillsMP : https://skillsmp.com/creators/code-yeongyu/oh-my-openagent/packages-shared-skills-skills-remove-ai-slops
- Dépôt    : https://github.com/code-yeongyu/oh-my-openagent/tree/dev/packages/shared-skills/skills/remove-ai-slops

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
