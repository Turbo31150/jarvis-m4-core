[user] ## Adversarial Claim Verifier (voter 1/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
État de l'art des « Agent Skills » (format SKILL.md avec frontmatter name/description, chargement progressif dans le contexte) : origine et spécification du format chez Anthropic, adoption réelle par l'écosystème (marketplaces type skillsmp.com, dépôts GitHub, compatibilité Claude Code / Codex CLI / ChatGPT), comparaison technique et fonctionnelle avec MCP (Model Context Protocol), les plugins Claude Code et les subagents — quand utiliser l'un plutôt que l'autre, bonnes pratiques de rédaction d'un skill (déclencheurs par mots-clés dans la description, taille, structure, scripts associés), et risques de sécurité liés à l'installation de skills tiers (injection de prompt, exécution de code, chaîne d'approvisionnement).

## Claim under review
"Anthropic's decision rule between Skills and subagents is that Skills are portable capabilities loadable by any Claude instance ("training materials"), whereas subagents are self-contained agents that handle workflows independently."

**Source:** https://claude.com/blog/skills-explained (primary)
**Supporting quote:** "Use Skills when: You want capabilities that any Claude instance can load and use. Skills are like training materials...Use subagents when: You need complete, self-contained agents designed for specific purposes that handle workflows independently."

## Checklist
1. Is the claim actually supported

[assistant] Primary source quote confirmed verbatim. Now checking whether Anthropic's own guidance elsewhere gives a different or more nuanced decision rule.

[assistant] Evidence is decisive. Let me verify the subagent-side doc to confirm the bidirectional relationship.