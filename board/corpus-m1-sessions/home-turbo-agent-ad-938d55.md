[user] ## Adversarial Claim Verifier (voter 2/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
État de l'art des « Agent Skills » (format SKILL.md avec frontmatter name/description, chargement progressif dans le contexte) : origine et spécification du format chez Anthropic, adoption réelle par l'écosystème (marketplaces type skillsmp.com, dépôts GitHub, compatibilité Claude Code / Codex CLI / ChatGPT), comparaison technique et fonctionnelle avec MCP (Model Context Protocol), les plugins Claude Code et les subagents — quand utiliser l'un plutôt que l'autre, bonnes pratiques de rédaction d'un skill (déclencheurs par mots-clés dans la description, taille, structure, scripts associés), et risques de sécurité liés à l'installation de skills tiers (injection de prompt, exécution de code, chaîne d'approvisionnement).

## Claim under review
"Le chargement progressif est spécifié en trois niveaux quantifiés : métadonnées (name + description) chargées au démarrage pour tous les skills (~100 tokens), corps du SKILL.md chargé seulement à l'activation (<5000 tokens recommandés), fichiers annexes chargés uniquement à la demande."

**Source:** https://agentskills.io/specification (primary)
**Supporting quote:** "1. **Metadata** (~100 tokens): The `name` and `description` fields are loaded at startup for all skills 2. **Instructions** (< 5000 tokens recommended): The full `SKILL.md` body is loaded when the skill is activated 3. **Resources** (as needed): F

[assistant] I'll verify this claim by checking the primary source and looking for contradicting evidence.

[assistant] Both the open specification site and Anthropic's own official documentation corroborate the claim verbatim, including the numeric table. I could not refute it.