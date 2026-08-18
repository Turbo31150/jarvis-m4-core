[user] ## Adversarial Claim Verifier (voter 1/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quelles sont, en 2026, les ressources les plus utilisées et les plus utiles pour outiller Claude Code et les agents de codage IA : catalogues de skills (skillsmp, awesome-claude-*, marketplaces), dépôts de sous-agents, serveurs MCP, patterns de slash commands, hooks. Pour chaque catégorie : qui l'utilise réellement, quelle traction mesurable (stars, téléchargements, adoption documentée), quelles limites connues. Contexte du demandeur : il exploite déjà un corpus local de 268 895 recettes extraites de 1 013 dépôts, 30 072 fiches de skills, 511 CLI et 319 agents. Ce qui l'intéresse n'est pas la liste des ressources mais CE QUI MANQUE dans un écosystème qui a déjà tout ça.

## Claim under review
"L'inventaire d'outils MCP d'un seul serveur officiel coûte déjà des dizaines de milliers de tokens de contexte : le serveur GitHub expose 94 outils pour ~17,6k tokens, celui d'Atlassian ~10k tokens pour Jira+Confluence."

**Source:** https://www.atlassian.com/blog/development/mcp-compression-preventing-tool-bloat-in-ai-agents (primary)
**Supporting quote:** "The official GitHub MCP server exposing 94 tools and consuming roughly 17.6k tokens. / The official Atlassian MCP server consuming roughly 10k tokens for Jira and Confluence tools alone."

## Checklist
1. Is the claim actually supported by the quote, or is it an overreach/misread?
2. WebSearch for contra

[assistant] Let me cross-check the article's framing and empirically count the GitHub MCP server's actual tool surface in this session.

[assistant] Local config shows the **default** official GitHub MCP server (no toolset flags). Let me count its actual tool surface and measure the real schema token cost.

[assistant] The `--help` output already confirms a documented `default` toolset (6 of 20 groups) vs `all`. Let me measure both configurations.

[assistant] Image is v1.7.0 (built 2026‑07‑23), CMD is `stdio`. The stdin was closing too early — let me hold it open.

[assistant] I have hard empirical data. Let me confirm the per-tool ratio implied by the claim versus reality.