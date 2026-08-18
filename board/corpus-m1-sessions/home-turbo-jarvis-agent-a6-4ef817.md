[user] ## Web Searcher: production / implémentation

Research question: "Comment les systèmes multi-agents en production pondèrent, routent et arbitrent entre agents en 2026 ? Techniques documentées : routage par score, vote pondéré, consensus, cascade de repli, sélection d'outils par embedding, bandits/apprentissage du routage. Pour chacune : preuves d'efficacité, coûts, modes de défaillance connus. Contexte : un routeur local pondère par popularité 0,3 + reproductibilité 0,5 + sûreté 0,2 pour choisir parmi 268 895 recettes réparties en 9 familles, avec 319 agents enregistrés. Question centrale : quelles pondérations et quels mécanismes d'arbitrage ont fait leurs preuves, et lesquels échouent silencieusement à l'échelle ?"

Your angle: **production / implémentation** — Retours d'ingénierie réels (blogs d'équipes, architectures d'orchestrateurs) sur la façon dont le routage et le repli sont câblés en prod, plutôt que sur le papier.
Search query: `production multi-agent LLM orchestration 2026 agent routing arbitration patterns weighted score fallback cascade engineering blog postmortem`

## Task
Use WebSearch with the query above (or a refined version). Return the top 4-6 most relevant results.
Rank by relevance to the ORIGINAL question, not just the search query. Skip obvious SEO spam/content farms.
Include a short snippet capturing why each result is relevant.

Structured output only.

[assistant] I'll search for production engineering material on multi-agent routing and arbitration.

[assistant] Two more targeted searches for engineering retrospectives and bandit/weighted-score routing.