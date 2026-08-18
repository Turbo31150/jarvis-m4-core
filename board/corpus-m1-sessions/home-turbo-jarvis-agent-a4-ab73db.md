[user] ## Adversarial Claim Verifier (voter 2/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quelles sont, en 2026, les ressources les plus utilisées et les plus utiles pour outiller Claude Code et les agents de codage IA : catalogues de skills (skillsmp, awesome-claude-*, marketplaces), dépôts de sous-agents, serveurs MCP, patterns de slash commands, hooks. Pour chaque catégorie : qui l'utilise réellement, quelle traction mesurable (stars, téléchargements, adoption documentée), quelles limites connues. Contexte du demandeur : il exploite déjà un corpus local de 268 895 recettes extraites de 1 013 dépôts, 30 072 fiches de skills, 511 CLI et 319 agents. Ce qui l'intéresse n'est pas la liste des ressources mais CE QUI MANQUE dans un écosystème qui a déjà tout ça.

## Claim under review
"La brique manquante identifiée par Atlassian est une couche d'indirection (découverte + invocation à la demande) qui remplace l'inventaire complet par trois méta-outils : get_tool_schema(tool_name), invoke_tool(tool_name, tool_input) et list_tools()."

**Source:** https://www.atlassian.com/blog/development/mcp-compression-preventing-tool-bloat-in-ai-agents (primary)
**Supporting quote:** "get_tool_schema(tool_name), invoke_tool(tool_name, tool_input), and optionally list_tools()"

## Checklist
1. Is the claim actually supported by the quote, or is it an overreach/misread?
2. WebSearch for contradicting evidence — does any credible source dispute or heavily q

[assistant] Let me cross-check the primary source with a different prompt to guard against summarizer hallucination.

[assistant] Verified against the primary source with two independent prompt runs. Findings:

**Confirmed:** the three tool names are verbatim, the source is primary (Atlassian engineering blog, Tim Esler, Senior Principal ML Engineer, 29 March 2026), current, and carries measured results (GitHub MCP server 17,600 → ~500 tokens).

**Refuted on two counts:**

1. **Architecture misstated.** The article says: *"The key move is to replace a server's full tool inventory with **two** generic wrapper tools"* — `get_tool_schema` and `invoke_tool`. `list_tools()` is explicitly *"For the most aggressive compression tier, we **optionally** add a third helper"*. The claim asserts a three-meta-tool design; the source describes 2 + 1 conditional. The supporting quote itself carries "and **optionally** list_tools()" — the word was dropped in the claim.

2. **"Brique manquante" is the researcher's framing, not Atlassian's, and is contradicted.** Atlassian presents this as an internal product response (*"We first developed this pattern inside Rovo Dev as a practical response to rising MCP prompt costs"*) and positions it as *"complementary options, not mutually exclusive"* alongside Cloudflare Code Mode and Anthropic's code execution with MCP. It never claims to identify an ecosystem gap. More decisively, the capability is not missing: Claude Code ships deferred tool loading natively — this very session's system prompt states *"The following deferred tools are now available via ToolSearch. Their schemas a