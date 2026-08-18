---
{
  "name": "writing-pr-descriptions",
  "source": "https://skillsmp.com/creators/posthog/posthog/agents-skills-writing-pr-descriptions",
  "repository": "https://github.com/PostHog/posthog/tree/master/.agents/skills/writing-pr-descriptions",
  "author": "PostHog",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:31:05+00:00",
  "verified": false,
  "quality_score": 95,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "c10a0d8abaca490db1de2afb1c2d5a9455f06ee1b0c0f65f890bffefc90cbb84"
}
---

# Résumé
Shapes a PR body into something a reviewer understands at a glance. Use ALWAYS before writing or editing a PR description, before `gh pr create` or `gh pr edit --body`, and when asked to improve an existing description. Puts the effect a person sees in the first line and the mechanism under it, routes each remaining fact to the form that carries it fastest (bullet, table, diagram, screenshot, collapsed block), cuts everything a reviewer does not need, then holds what survives to a checkable shape: one fact per bullet, sentences under 25 words, active voice, no idioms. Makes the body stand alone, so a reader who opens no files still knows why the PR is necessary and what it does, sizes the body to the change so a small PR reads as small, and makes every claim either linked to its evidence or labeled as unchecked. Ends with a scan test the agent runs over its own draft, reading only the title and the first line of two sections. Not for commit messages (see AGENTS.md, "Commit types") or user-facing product copy 

# Source originale
- SkillsMP : https://skillsmp.com/creators/posthog/posthog/agents-skills-writing-pr-descriptions
- Dépôt    : https://github.com/PostHog/posthog/tree/master/.agents/skills/writing-pr-descriptions

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
