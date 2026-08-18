[user] ## Adversarial Claim Verifier (voter 1/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
État de l'art des « Agent Skills » (format SKILL.md avec frontmatter name/description, chargement progressif dans le contexte) : origine et spécification du format chez Anthropic, adoption réelle par l'écosystème (marketplaces type skillsmp.com, dépôts GitHub, compatibilité Claude Code / Codex CLI / ChatGPT), comparaison technique et fonctionnelle avec MCP (Model Context Protocol), les plugins Claude Code et les subagents — quand utiliser l'un plutôt que l'autre, bonnes pratiques de rédaction d'un skill (déclencheurs par mots-clés dans la description, taille, structure, scripts associés), et risques de sécurité liés à l'installation de skills tiers (injection de prompt, exécution de code, chaîne d'approvisionnement).

## Claim under review
"Seuls deux champs de frontmatter sont obligatoires — `name` (max 64 caractères, minuscules/chiffres/tirets, devant correspondre au nom du dossier parent) et `description` (max 1024 caractères) — les champs `license`, `compatibility` (max 500 car.), `metadata` et `allowed-tools` étant optionnels, ce dernier étant explicitement marqué expérimental."

**Source:** https://agentskills.io/specification (primary)
**Supporting quote:** "| `name` | Yes | Max 64 characters. Lowercase letters, numbers, and hyphens only. Must not start or end with a hyphen. | | `description` | Yes | Max 1024 characters. Non-empty. Describe

[assistant] Let me cross-check against Anthropic's own primary documentation and verify who maintains agentskills.io.

[assistant] Let me check Claude Code's implementation docs for any additional/conflicting frontmatter fields.