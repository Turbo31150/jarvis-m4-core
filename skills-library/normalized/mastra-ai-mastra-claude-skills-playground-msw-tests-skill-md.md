---
{
  "name": "playground-msw-tests",
  "source": "https://skillsmp.com/creators/mastra-ai/mastra/claude-skills-playground-msw-tests",
  "repository": "https://github.com/mastra-ai/mastra/tree/main/.claude/skills/playground-msw-tests",
  "author": "mastra-ai",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:28:30+00:00",
  "verified": false,
  "quality_score": 95,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "a94f68f5fe5400c8725387c7e8f359526a1704b0c90f0bbb4d0d39ebd6412407"
}
---

# Résumé
REQUIRED and PRIMARY testing approach for packages/playground and packages/playground-ui. Triggers on: adding or modifying hooks, pages, route components, data-fetching code, React Query interactions, or any test work in these packages. Generates Vitest tests that drive the real @mastra/client-js + React Query stack through MSW handlers and typed fixtures derived from @mastra/client-js response types. This is the #1 way to test the playground packages — ABOVE Playwright E2E. Use Playwright only for cross-page user journeys that MSW cannot model.

# Source originale
- SkillsMP : https://skillsmp.com/creators/mastra-ai/mastra/claude-skills-playground-msw-tests
- Dépôt    : https://github.com/mastra-ai/mastra/tree/main/.claude/skills/playground-msw-tests

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
