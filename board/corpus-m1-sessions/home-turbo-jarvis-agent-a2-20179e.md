[user] ## Adversarial Claim Verifier (voter 1/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quelles sont, en 2026, les ressources les plus utilisées et les plus utiles pour outiller Claude Code et les agents de codage IA : catalogues de skills (skillsmp, awesome-claude-*, marketplaces), dépôts de sous-agents, serveurs MCP, patterns de slash commands, hooks. Pour chaque catégorie : qui l'utilise réellement, quelle traction mesurable (stars, téléchargements, adoption documentée), quelles limites connues. Contexte du demandeur : il exploite déjà un corpus local de 268 895 recettes extraites de 1 013 dépôts, 30 072 fiches de skills, 511 CLI et 319 agents. Ce qui l'intéresse n'est pas la liste des ressources mais CE QUI MANQUE dans un écosystème qui a déjà tout ça.

## Claim under review
"17,2 % des serveurs MCP distants mesurés (1 603 sur 9 326) sont morts / injoignables au moment du sondage : le catalogue déclare beaucoup plus de capacités qu'il n'en exécute réellement."

**Source:** https://mcpqueen.com/reports/state-of-mcp-2026-07 (primary)
**Supporting quote:** "9,326 remotes we grade, 7,723 (82.8%) are reachable right now. 1,603 (17.2%) are dead"

## Checklist
1. Is the claim actually supported by the quote, or is it an overreach/misread?
2. WebSearch for contradicting evidence — does any credible source dispute or heavily qualify this?
3. Is the source quality sufficient for the claim's strength? (extraordinary claims need primary sour

[assistant] Key methodological signal spotted — the registry returns multiple **versions** per server name. Let me test whether that inflates the "dead" count.

[assistant] The first-page sample is alphabetically biased. Let me draw a larger, spread-out sample across the registry.

[assistant] Striking: **817 remote rows collapse to only 119 unique URLs and 149 unique server names.** Let me probe those unique endpoints.

[assistant] I have enough to render a verdict. Let me capture the exact replication numbers.

[assistant] **Verdict: refuted.** The quote is accurate, but the number fails independent replication and comes from a vendor with direct commercial interest in the finding.