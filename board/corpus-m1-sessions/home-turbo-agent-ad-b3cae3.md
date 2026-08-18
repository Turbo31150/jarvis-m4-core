[user] ## Adversarial Claim Verifier (voter 3/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
État de l'art des « Agent Skills » (format SKILL.md avec frontmatter name/description, chargement progressif dans le contexte) : origine et spécification du format chez Anthropic, adoption réelle par l'écosystème (marketplaces type skillsmp.com, dépôts GitHub, compatibilité Claude Code / Codex CLI / ChatGPT), comparaison technique et fonctionnelle avec MCP (Model Context Protocol), les plugins Claude Code et les subagents — quand utiliser l'un plutôt que l'autre, bonnes pratiques de rédaction d'un skill (déclencheurs par mots-clés dans la description, taille, structure, scripts associés), et risques de sécurité liés à l'installation de skills tiers (injection de prompt, exécution de code, chaîne d'approvisionnement).

## Claim under review
"Anthropic identifie explicitement le risque d'approvisionnement lié aux skills tiers et recommande de n'installer que depuis des sources de confiance, d'auditer les skills moins fiables, et de surveiller les dépendances de code, les ressources embarquées et les instructions poussant Claude vers des sources réseau externes non fiables."

**Source:** https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills (primary)
**Supporting quote:** "Installing skills only from trusted sources. When installing a skill from a less-trusted source, thoroughly audit it before use."

## Checklis

[assistant] The fetched text matches the claim closely. Let me corroborate independently and check for contradicting evidence.

[assistant] Verification complete. The primary source text matches the claim element-for-element, and a second independent Anthropic source (platform docs) corroborates it.