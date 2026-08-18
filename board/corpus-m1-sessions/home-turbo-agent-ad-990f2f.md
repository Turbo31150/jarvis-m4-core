[user] ## Adversarial Claim Verifier (voter 3/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
État de l'art des « Agent Skills » (format SKILL.md avec frontmatter name/description, chargement progressif dans le contexte) : origine et spécification du format chez Anthropic, adoption réelle par l'écosystème (marketplaces type skillsmp.com, dépôts GitHub, compatibilité Claude Code / Codex CLI / ChatGPT), comparaison technique et fonctionnelle avec MCP (Model Context Protocol), les plugins Claude Code et les subagents — quand utiliser l'un plutôt que l'autre, bonnes pratiques de rédaction d'un skill (déclencheurs par mots-clés dans la description, taille, structure, scripts associés), et risques de sécurité liés à l'installation de skills tiers (injection de prompt, exécution de code, chaîne d'approvisionnement).

## Claim under review
"Le chargement se fait par divulgation progressive à trois niveaux : les métadonnées de tous les skills installés sont chargées au démarrage, le contenu complet du SKILL.md seulement si Claude juge le skill pertinent, et les fichiers additionnels du dossier uniquement à la demande — ce qui rend le contexte empaquetable dans un skill « effectivement illimité »."

**Source:** https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills (primary)
**Supporting quote:** "skills let Claude load information only as needed ... the amount of context that can be bundled into a skill is effec

[assistant] Primary source strongly matches. Now let me hunt for qualifications and contradictions.

[assistant] Both the primary engineering post and the official platform docs confirm the claim in near-verbatim terms. Let me record the verdict.