---
{
  "name": "writing-tests",
  "source": "https://skillsmp.com/creators/posthog/posthog/agents-skills-writing-tests",
  "repository": "https://github.com/PostHog/posthog/tree/master/.agents/skills/writing-tests",
  "author": "PostHog",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:31:03+00:00",
  "verified": false,
  "quality_score": 95,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "e6e3bed5df3237255d195e85a8dded77f3202bd970a30d9e8f52e79df67e7227"
}
---

# Résumé
Gates whether a new test should exist and forces it to be efficient, protecting CI from low-value test bloat. Use before adding or substantially changing any pytest, Jest, or Playwright test — whenever an agent or engineer is about to write tests for a new feature, bugfix, or PR. Front-loads the value bar (every test must catch a realistic regression no existing test already catches; test behavior through the public interface, not implementation details; collapse near-duplicates into parameterized cases) and the efficiency bar (deterministic, isolated, fast; pick the cheapest test level; Django TestCase over TransactionTestCase; no sleeps, no real network). Includes a "don't write it" decision tree. For fixing an existing flaky test use `/fixing-flaky-tests`; after this gate says a Playwright test is warranted, use `/playwright-test` for mechanics.

# Source originale
- SkillsMP : https://skillsmp.com/creators/posthog/posthog/agents-skills-writing-tests
- Dépôt    : https://github.com/PostHog/posthog/tree/master/.agents/skills/writing-tests

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
