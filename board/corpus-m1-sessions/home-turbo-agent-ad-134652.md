[user] ## Adversarial Claim Verifier (voter 2/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
État de l'art des « Agent Skills » (format SKILL.md avec frontmatter name/description, chargement progressif dans le contexte) : origine et spécification du format chez Anthropic, adoption réelle par l'écosystème (marketplaces type skillsmp.com, dépôts GitHub, compatibilité Claude Code / Codex CLI / ChatGPT), comparaison technique et fonctionnelle avec MCP (Model Context Protocol), les plugins Claude Code et les subagents — quand utiliser l'un plutôt que l'autre, bonnes pratiques de rédaction d'un skill (déclencheurs par mots-clés dans la description, taille, structure, scripts associés), et risques de sécurité liés à l'installation de skills tiers (injection de prompt, exécution de code, chaîne d'approvisionnement).

## Claim under review
"The same skill folders are portable across three Anthropic surfaces: Claude Code (installed via the plugin-marketplace mechanism, i.e. skills are distributed as Claude Code plugins), Claude.ai (pre-loaded for paid plans, custom upload possible), and the Claude API (Skills API) — and in Claude Code a skill is triggered simply by mentioning it."

**Source:** https://github.com/anthropics/skills (primary)
**Supporting quote:** "You can register this repository as a Claude Code Plugin marketplace by running the following command in Claude Code:
```
/plugin marketplace add anthropics/skills
```
[…] After installing 

[assistant] I'll verify this claim by examining the primary source and searching for contradicting evidence.

[assistant] Let me check the official docs for how skills are actually installed and triggered in Claude Code.

[assistant] I have strong primary-source evidence. Let me do one final check on the Claude Code skills doc to confirm the installation mechanisms.

[assistant] I have enough evidence. The primary source documentation directly contradicts multiple parts of the claim.