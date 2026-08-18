[user] ## Web Searcher: broad/primary — validation des recettes d'agents et runbooks

Research question: "Comment les projets sérieux valident-ils qu'une recette d'agent publiée (SKILL.md, playbook, runbook) est réellement rejouable ? État de l'art 2026 sur : détection de placeholders et de trous de configuration, vérification statique de scripts shell sans les exécuter, mesure de reproductibilité multi-environnement, taux de recettes publiées réellement exécutables constatés dans la littérature ou les audits publics. Contexte : une chaîne locale mesure 0,583 de score de reproductibilité et 34 % de recettes 100 % jouables via simulation statique (binaire présent + absence de placeholder), sous 3 profils d'environnement. Question centrale : cette méthode est-elle conforme à l'état de l'art, que rate-t-elle, et quelles techniques éprouvées l'amélioreraient ?"

Your angle: **broad/primary — validation des recettes d'agents et runbooks** — Cadre l'état de l'art praticien : comment les projets d'agents (Anthropic Agent Skills, MCP, Ansible playbooks, SRE runbooks) prouvent qu'une recette publiée tourne vraiment.
Search query: `validating agent skills SKILL.md playbook runbook reproducibility CI linting executable documentation testing 2026`

## Task
Use WebSearch with the query above (or a refined version). Return the top 4-6 most relevant results.
Rank by relevance to the ORIGINAL question, not just the search query. Skip obvious SEO spam/content farms.
Include a short snippet capturing

[assistant] I'll search for state-of-the-art practices on validating agent recipes and runbooks.

[assistant] Two more targeted searches to cover the empirical rates and multi-environment reproducibility literature.