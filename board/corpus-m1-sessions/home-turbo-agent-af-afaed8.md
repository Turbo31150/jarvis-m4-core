[user] ## Web Searcher: Comparaison architecturale

Research question: "État de l'art des « Agent Skills » (format SKILL.md avec frontmatter name/description, chargement progressif dans le contexte) : origine et spécification du format chez Anthropic, adoption réelle par l'écosystème (marketplaces type skillsmp.com, dépôts GitHub, compatibilité Claude Code / Codex CLI / ChatGPT), comparaison technique et fonctionnelle avec MCP (Model Context Protocol), les plugins Claude Code et les subagents — quand utiliser l'un plutôt que l'autre, bonnes pratiques de rédaction d'un skill (déclencheurs par mots-clés dans la description, taille, structure, scripts associés), et risques de sécurité liés à l'installation de skills tiers (injection de prompt, exécution de code, chaîne d'approvisionnement)."

Your angle: **Comparaison architecturale** — Isoler les essais techniques et docs comparant les quatre mécanismes d'extension : coût en tokens de contexte, statique vs connecté, déterminisme, granularité — pour produire une grille de décision.
Search query: `Claude Skills vs MCP vs plugins vs subagents when to use which context window token cost comparison architecture`

## Task
Use WebSearch with the query above (or a refined version). Return the top 4-6 most relevant results.
Rank by relevance to the ORIGINAL question, not just the search query. Skip obvious SEO spam/content farms.
Include a short snippet capturing why each result is relevant.

Structured output only.

[assistant] Let me refine with a second search focused on progressive disclosure and token economics.

[assistant] Sources: [Skills explained (Anthropic)](https://claude.com/blog/skills-explained) · [arXiv 2602.12430](https://arxiv.org/html/2602.12430v3) · [SwirlAI](https://www.newsletter.swirlai.com/p/agent-skills-progressive-disclosure) · [Awesome Skills](https://awesomeskill.ai/blog/skills-vs-mcp-vs-plugins-vs-subagents) · [Claude Code Docs](https://code.claude.com/docs/en/features-overview) · [Smith Horn Group](https://smithhorngroup.substack.com/p/choosing-between-skills-subagents)