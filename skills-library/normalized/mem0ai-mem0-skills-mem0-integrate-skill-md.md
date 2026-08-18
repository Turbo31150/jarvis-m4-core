---
{
  "name": "mem0-integrate",
  "source": "https://skillsmp.com/creators/mem0ai/mem0/skills-mem0-integrate",
  "repository": "https://github.com/mem0ai/mem0/tree/main/skills/mem0-integrate",
  "author": "mem0ai",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:28:03+00:00",
  "verified": false,
  "quality_score": 95,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "e18e4be806a8a7b27c4a16bfd76f23d7668c233dcc3a6eb4ebf5980b6de25db8"
}
---

# Résumé
Integrate Mem0 into an existing repository using a goal-driven, TDD pipeline. Detects the repo's language automatically and asks the user to pick between Mem0 Platform (managed) and Mem0 Open Source (self-hosted). Writes failing tests before any implementation. Produces a local feature branch plus `.mem0-integration/` artifacts consumed by the paired verification skill. TRIGGER when: user says "integrate mem0", "add mem0 to this repo", "wire mem0 into <repo>", or asks how to add memory to an existing project. DO NOT TRIGGER when: the user wants general SDK usage (use skill:mem0), CLI usage (use skill:mem0-cli), or Vercel AI SDK (use skill:mem0-vercel-ai-sdk). After success, invoke skill:mem0-test-integration to verify in the same workspace (loose coupling).

# Source originale
- SkillsMP : https://skillsmp.com/creators/mem0ai/mem0/skills-mem0-integrate
- Dépôt    : https://github.com/mem0ai/mem0/tree/main/skills/mem0-integrate

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
