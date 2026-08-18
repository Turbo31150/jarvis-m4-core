---
{
  "name": "doordash-spend-guard",
  "source": "https://skillsmp.com/creators/davila7/claude-code-templates/cli-tool-components-skills-doordash-doordash-spend-guard",
  "repository": "https://github.com/davila7/claude-code-templates/tree/main/cli-tool/components/skills/doordash/doordash-spend-guard",
  "author": "davila7",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:31:10+00:00",
  "verified": false,
  "quality_score": 95,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "d0842bdb49ec03a58b699c0a4f25ad35c1c5342b68efe2c1611cf28da185ecc0"
}
---

# Résumé
Hard spending policy for agent-driven DoorDash ordering through the DoorDash CLI (dd-cli). Per-order ceiling, daily/weekly/monthly caps, cooldown between orders, and blocked hours — enforced deterministically by routing every cart-mutation and checkout through the dd-guard wrapper script, which prices the cart, checks the policy against a persistent spend ledger, and refuses out-of-policy checkouts with exit code 2. Use when the user wants budget limits on agent food ordering, asks "how much have I spent on DoorDash", wants to set spending caps, or whenever building carts / checking out with dd-cli while this skill is installed. Pairs with a PreToolUse hook that denies raw dd-cli checkout calls that bypass the wrapper.

# Source originale
- SkillsMP : https://skillsmp.com/creators/davila7/claude-code-templates/cli-tool-components-skills-doordash-doordash-spend-guard
- Dépôt    : https://github.com/davila7/claude-code-templates/tree/main/cli-tool/components/skills/doordash/doordash-spend-guard

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
