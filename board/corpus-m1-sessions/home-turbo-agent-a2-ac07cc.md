[user] ## Adversarial Claim Verifier (voter 3/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
État de l'art des « Agent Skills » (format SKILL.md avec frontmatter name/description, chargement progressif dans le contexte) : origine et spécification du format chez Anthropic, adoption réelle par l'écosystème (marketplaces type skillsmp.com, dépôts GitHub, compatibilité Claude Code / Codex CLI / ChatGPT), comparaison technique et fonctionnelle avec MCP (Model Context Protocol), les plugins Claude Code et les subagents — quand utiliser l'un plutôt que l'autre, bonnes pratiques de rédaction d'un skill (déclencheurs par mots-clés dans la description, taille, structure, scripts associés), et risques de sécurité liés à l'installation de skills tiers (injection de prompt, exécution de code, chaîne d'approvisionnement).

## Claim under review
"Progressive disclosure is specified in three levels with explicit budgets: name+description (~100 tokens) loaded at startup for every installed skill, the full SKILL.md body (recommended <5000 tokens) loaded only on activation, and bundled files loaded only when required; the main SKILL.md should stay under 500 lines."

**Source:** https://github.com/anthropics/skills/blob/main/spec/agent-skills-spec.md (primary)
**Supporting quote:** "1. **Metadata** (~100 tokens): The `name` and `description` fields are loaded at startup for all skills
2. **Instructions** (< 5000 tokens recommended): The full `SKILL.md` body 

[assistant] The canonical spec confirms it verbatim. Let me check for contradicting/qualifying evidence and the source-staleness issue.

[assistant] Verified against the canonical primary source and corroborated in Claude Code docs. Reporting.