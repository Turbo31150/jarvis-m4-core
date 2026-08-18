[user] ## Adversarial Claim Verifier (voter 1/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
État de l'art des « Agent Skills » (format SKILL.md avec frontmatter name/description, chargement progressif dans le contexte) : origine et spécification du format chez Anthropic, adoption réelle par l'écosystème (marketplaces type skillsmp.com, dépôts GitHub, compatibilité Claude Code / Codex CLI / ChatGPT), comparaison technique et fonctionnelle avec MCP (Model Context Protocol), les plugins Claude Code et les subagents — quand utiliser l'un plutôt que l'autre, bonnes pratiques de rédaction d'un skill (déclencheurs par mots-clés dans la description, taille, structure, scripts associés), et risques de sécurité liés à l'installation de skills tiers (injection de prompt, exécution de code, chaîne d'approvisionnement).

## Claim under review
"The canonical Agent Skills spec has been moved out of the anthropics/skills GitHub repo: the file spec/agent-skills-spec.md is now a one-line stub pointing to agentskills.io/specification, indicating the format has been externalized as an ecosystem standard rather than kept as Anthropic repo documentation (last commit on that path: 2025-12-20)."

**Source:** https://github.com/anthropics/skills/blob/main/spec/agent-skills-spec.md (primary)
**Supporting quote:** "# Agent Skills Spec

The spec is now located at <https://agentskills.io/specification>"

## Checklist
1. Is the claim actually supported by the quote, 

[assistant] Quote confirmed. Now the two load-bearing sub-claims: the commit date, and the interpretation that this means "ecosystem standard rather than Anthropic documentation."

[assistant] Confirmed: last commit on that path is 2025-12-20 (SHA 69c0b1a). Now testing the interpretive claim — is agentskills.io genuinely externalized, or just Anthropic under a neutral domain?

[assistant] All three components verified against primary sources. Let me record the finding.