[user] ## Adversarial Claim Verifier (voter 3/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quelles sont, en 2026, les ressources les plus utilisées et les plus utiles pour outiller Claude Code et les agents de codage IA : catalogues de skills (skillsmp, awesome-claude-*, marketplaces), dépôts de sous-agents, serveurs MCP, patterns de slash commands, hooks. Pour chaque catégorie : qui l'utilise réellement, quelle traction mesurable (stars, téléchargements, adoption documentée), quelles limites connues. Contexte du demandeur : il exploite déjà un corpus local de 268 895 recettes extraites de 1 013 dépôts, 30 072 fiches de skills, 511 CLI et 319 agents. Ce qui l'intéresse n'est pas la liste des ressources mais CE QUI MANQUE dans un écosystème qui a déjà tout ça.

## Claim under review
"Les registres MCP publient massivement des fiches non exécutables : jusqu'à 10,11 % de serveurs sans README (MCP Store), 6,75 % de liens invalides (mcp.so) et 4,25 % de fiches au contenu vide (MCP Store) — la métadonnée de catalogue ne garantit ni l'existence ni l'exécutabilité de la ressource."

**Source:** https://arxiv.org/html/2510.16558 (primary)
**Supporting quote:** "mcp.so: 6.75% invalid links, 0.07% empty content, 1.04% missing README ... MCP Store: 0.18% invalid links, 4.25% empty, 10.11% missing README"

## Checklist
1. Is the claim actually supported by the quote, or is it an overreach/misread?
2. WebSearch for contradicting evidence — does any c

[assistant] The quote matches Table III. Now let me check the registry sizes and the definitions behind these metrics, since the claim's framing depends on them.

[assistant] The numbers are verbatim accurate. Now checking whether the interpretive framing survives, and whether 2025 data still holds in 2026.

[assistant] I verified the claim against the primary source verbatim, checked the authors' own definitions of each metric, and checked whether the 2025 measurement window still describes 2026.

**What holds:** The three numbers are exact. Table III of arXiv:2510.16558v2 ("A First Look at the Security Issues in the Model Context Protocol Ecosystem", Li & Gao, U. Delaware, DSN 2026, submitted 18 Oct 2025) reads verbatim: mcp.so 6.75 / 0.07 / 1.04; MCP Market 3.30 / 0 / 0.29; MCP Store 0.18 / 4.25 / 10.11; Pulse MCP 0.14 / 0.04 / 1.73. Sample = 67,057 servers across six registries. Good primary source.

**What breaks:** three independent problems with the framing.

1. "non exécutables" is measured nowhere. The authors define the metrics as HTTP status checks (200/404), a GitHub API call for empty repos, and a file-presence check for README. No server was ever executed. Their own definition of the third metric: "missing configurations, where the server content exists but lacks configuration examples, making it unclear how the server should be used" — a documentation defect, explicitly about user comprehension, not runtime failure. The claim converts a README-presence check into an executability verdict.

2. "massivement" is a max-per-column stack. The claim takes the worst registry on each of three different axes and welds them into one sentence. No registry is bad on more than one axis: mcp.so's missing-README rate is 1.04%, MCP Store's invalid-link rate is 0.18%. The paper's very next sent