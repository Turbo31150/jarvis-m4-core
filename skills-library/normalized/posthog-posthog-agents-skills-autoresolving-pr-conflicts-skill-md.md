---
{
  "name": "autoresolving-pr-conflicts",
  "source": "https://skillsmp.com/creators/posthog/posthog/agents-skills-autoresolving-pr-conflicts",
  "repository": "https://github.com/PostHog/posthog/tree/master/.agents/skills/autoresolving-pr-conflicts",
  "author": "PostHog",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:31:03+00:00",
  "verified": false,
  "quality_score": 95,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "55b360ae3f0669ec8cf1107d5de0789d4b1e30b9acadabd884646a72279b05f0"
}
---

# Résumé
Operating procedure for the conflict-autoresolver agent: sweep open PostHog/posthog PRs that conflict with master, resolve the trivial conflicts (generated artifacts deterministically, source conflicts with judgment), land a single signed commit on the PR head, and flag everything else for a human. Use when running as the "Autoresolve PR conflicts" Loop, when asked to sweep or auto-resolve merge conflicts against master, or when asked to bring a conflicting PR up to date without rewriting its history. Trigger terms: conflict sweep, autoresolve, merge conflicts, conflicting PRs, bring PR up to date, restack. Operators setting up the Loop itself: see references/loop-setup.md.

# Source originale
- SkillsMP : https://skillsmp.com/creators/posthog/posthog/agents-skills-autoresolving-pr-conflicts
- Dépôt    : https://github.com/PostHog/posthog/tree/master/.agents/skills/autoresolving-pr-conflicts

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
