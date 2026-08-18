[user] ## Adversarial Claim Verifier (voter 2/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
État de l'art des « Agent Skills » (format SKILL.md avec frontmatter name/description, chargement progressif dans le contexte) : origine et spécification du format chez Anthropic, adoption réelle par l'écosystème (marketplaces type skillsmp.com, dépôts GitHub, compatibilité Claude Code / Codex CLI / ChatGPT), comparaison technique et fonctionnelle avec MCP (Model Context Protocol), les plugins Claude Code et les subagents — quand utiliser l'un plutôt que l'autre, bonnes pratiques de rédaction d'un skill (déclencheurs par mots-clés dans la description, taille, structure, scripts associés), et risques de sécurité liés à l'installation de skills tiers (injection de prompt, exécution de code, chaîne d'approvisionnement).

## Claim under review
"Le format Agent Skill est spécifié par Anthropic comme un fichier SKILL.md à frontmatter YAML dont seuls `name` et `description` sont requis, avec des contraintes strictes : name ≤ 64 caractères, minuscules/chiffres/tirets uniquement, sans balises XML et sans les mots réservés « anthropic » et « claude » ; description non vide et ≤ 1024 caractères."

**Source:** https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview (primary)
**Supporting quote:** "**Required fields:** `name` and `description`

`name`:

* Maximum 64 characters
* Must contain only lowercase letters, numbers, and hyphens
* Can

[assistant] The primary source confirms the quote verbatim. Let me check for contradictions or surface-specific divergences.

[assistant] The open spec differs. Let me check the Claude Code doc and test empirically against real installed skills.

[assistant] I verified the primary source directly and cross-checked against the open standard and Claude Code's implementation.

[assistant] Verification complete. Findings:

**Primary source confirms the quote verbatim.** I fetched `https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview` and the "Skill structure" section reproduces the supporting quote word-for-word: "**Required fields:** `name` and `description`", with `name` = max 64 chars, lowercase letters/numbers/hyphens only, no XML tags, no reserved words "anthropic"/"claude"; `description` = non-empty, max 1024 chars, no XML tags. Current (page covers Opus-era surfaces, Claude Platform on AWS, Microsoft Foundry), primary, non-marketing.

**But three real scope qualifications surfaced that the claim's framing ("le format Agent Skill est spécifié par Anthropic") papers over:**

1. **The vendor-neutral spec at agentskills.io — which Claude Code's own docs say it follows ("Claude Code skills follow the [Agent Skills](https://agentskills.io) open standard") — does NOT contain the reserved-word rule at all.** It lists `name`: max 64 chars, lowercase alphanumeric + hyphens, must not start/end with a hyphen, no consecutive hyphens, must match the parent directory name. No mention of "anthropic"/"claude" being forbidden, and no XML-tag prohibition. It also defines four optional fields (`license`, `compatibility` ≤500 chars, `metadata`, `allowed-tools`).

2. **In Claude Code, `name` is not required at all.** The Claude Code skills doc states: "All fields are optional. Only `description` is recommended so Claude knows when to use the skill." Its 