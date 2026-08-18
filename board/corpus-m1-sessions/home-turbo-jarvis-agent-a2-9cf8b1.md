[user] ## Adversarial Claim Verifier (voter 2/3)

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

[assistant] Search budget is exhausted. Let me verify independently via direct fetches and local tooling.

[assistant] I have enough to adjudicate. Let me do one last check — count what the official GitHub MCP server actually exposes on this production machine.

[assistant] Verification complete. Assessment below.

**What holds up:** the two numbers are quoted verbatim and accurately from a primary source — Atlassian engineering blog, Tim Esler (Senior Principal ML Engineer), 29 March 2026, recent enough for a fast-moving field. The figures are also internally coherent (17.6k / 94 ≈ 187 tokens per tool definition, exactly the right order for name + description + JSON schema), so they are not fabricated.

**What breaks:**

1. **Arithmetic overreach in the claim's own framing.** The claim opens with "coûte déjà des **dizaines de milliers** de tokens … pour **un seul serveur**." Its own cited figures are 17.6k and 10k — both *below* 20k. The source's "30k+" figure explicitly applies to **combining multiple** servers, not one. The headline generalization contradicts the evidence offered to support it.

2. **94 tools is a non-default maximum presented as the norm.** The official `github/github-mcp-server` README confirms a **reduced default toolset** (`context`, `repos`, `issues`, `pull_requests`, `users`) out of 22 available toolsets; 94 requires opting into `--toolsets all`. Empirically, on this machine's live production install (August 2026) the official GitHub MCP server exposes **44 tools**, not 94 — under half the cited figure. The README even states enabling only needed toolsets "can help the LLM with tool choice and reduce the context size." The upstream server has also since consolidated tools (`issue_read`/`issue_write`, `pull_request_read`