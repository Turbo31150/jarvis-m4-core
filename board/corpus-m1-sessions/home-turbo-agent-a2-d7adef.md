[user] ## Adversarial Claim Verifier (voter 2/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
État de l'art des « Agent Skills » (format SKILL.md avec frontmatter name/description, chargement progressif dans le contexte) : origine et spécification du format chez Anthropic, adoption réelle par l'écosystème (marketplaces type skillsmp.com, dépôts GitHub, compatibilité Claude Code / Codex CLI / ChatGPT), comparaison technique et fonctionnelle avec MCP (Model Context Protocol), les plugins Claude Code et les subagents — quand utiliser l'un plutôt que l'autre, bonnes pratiques de rédaction d'un skill (déclencheurs par mots-clés dans la description, taille, structure, scripts associés), et risques de sécurité liés à l'installation de skills tiers (injection de prompt, exécution de code, chaîne d'approvisionnement).

## Claim under review
"Anthropic documente explicitement le risque de chaîne d'approvisionnement et d'injection de prompt : n'utiliser que des skills de sources de confiance, auditer tous les fichiers embarqués, considérer comme particulièrement risqués les skills qui récupèrent des données depuis des URL externes (le contenu récupéré pouvant contenir des instructions malveillantes), et traiter l'installation d'un skill comme l'installation d'un logiciel."

**Source:** https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview (primary)
**Supporting quote:** "Use Skills only from trusted sources: those you created you

[assistant] Primary source confirms the quote verbatim. Now checking for contradicting evidence and terminology precision.

[assistant] Verification complete. I fetched the live primary source and every element of the claim appears verbatim, plus found a second corroborating Anthropic page.