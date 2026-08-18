---
{
  "name": "posthog-desktop",
  "source": "https://skillsmp.com/creators/posthog/posthog/agents-skills-posthog-desktop",
  "repository": "https://github.com/PostHog/posthog/tree/master/.agents/skills/posthog-desktop",
  "author": "PostHog",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:31:03+00:00",
  "verified": false,
  "quality_score": 95,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "7cc76c5201e5b42c50b7e14940b8c4c56ea84266c6ae3ebf0c2dc62a414c8fba"
}
---

# Résumé
Scopes work to the desktop app at products/desktop — a nested standalone pnpm/turbo/Biome workspace imported from PostHog/code, not part of the root frontend or Django build. Use when the user says /posthog-desktop, or works on the Electron desktop app, apps/code, apps/web, apps/mobile, packages/core, packages/ui, packages/workspace-server, @posthog/api-client, @posthog/agent, or the agent framework. Pins the working directory to products/desktop, swaps in that tree's toolchain and conventions in place of the monorepo's, and defines the few paths outside the tree that may be touched (Django APIs the app calls, desktop-* CI, resync config).

# Source originale
- SkillsMP : https://skillsmp.com/creators/posthog/posthog/agents-skills-posthog-desktop
- Dépôt    : https://github.com/PostHog/posthog/tree/master/.agents/skills/posthog-desktop

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
