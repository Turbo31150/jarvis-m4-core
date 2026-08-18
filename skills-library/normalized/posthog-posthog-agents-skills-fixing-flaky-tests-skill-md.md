---
{
  "name": "fixing-flaky-tests",
  "source": "https://skillsmp.com/creators/posthog/posthog/agents-skills-fixing-flaky-tests",
  "repository": "https://github.com/PostHog/posthog/tree/master/.agents/skills/fixing-flaky-tests",
  "author": "PostHog",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:31:03+00:00",
  "verified": false,
  "quality_score": 95,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "42d64527aede198c6254feb0116b147496bb3dc6b991e0578f602b5fae710f72"
}
---

# Résumé
Guides an agent through reproducing, root-causing, fixing, and validating flaky tests in the PostHog monorepo. Use when a test fails intermittently in CI but passes on rerun or locally, when `hogli ci:insights` or the debugging-ci-failures skill classifies a failure as a flaky test, when given a GitHub Actions URL for a flaky job, or when asked to deflake, stabilize, or fix a flaky Jest, pytest, or Playwright test. Core discipline: reproduce locally before changing anything, fix the root cause (never mask it with sleeps, retries, or bigger timeouts), and prove the fix with an N-run validation loop sized to the observed failure rate. Stabilizing is not the only valid outcome — the skill also gates whether the test should exist, so deleting a test that catches nothing real, or re-leveling one that flakes because of the level it runs at, are first-class endings.

# Source originale
- SkillsMP : https://skillsmp.com/creators/posthog/posthog/agents-skills-fixing-flaky-tests
- Dépôt    : https://github.com/PostHog/posthog/tree/master/.agents/skills/fixing-flaky-tests

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
