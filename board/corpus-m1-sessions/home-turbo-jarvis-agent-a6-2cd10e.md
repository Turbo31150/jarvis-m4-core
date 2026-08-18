[user] ## Web Searcher: contrarian/limites — trous de config, placeholders et faux négatifs du statique

Research question: "Comment les projets sérieux valident-ils qu'une recette d'agent publiée (SKILL.md, playbook, runbook) est réellement rejouable ? État de l'art 2026 sur : détection de placeholders et de trous de configuration, vérification statique de scripts shell sans les exécuter, mesure de reproductibilité multi-environnement, taux de recettes publiées réellement exécutables constatés dans la littérature ou les audits publics. Contexte : une chaîne locale mesure 0,583 de score de reproductibilité et 34 % de recettes 100 % jouables via simulation statique (binaire présent + absence de placeholder), sous 3 profils d'environnement. Question centrale : cette méthode est-elle conforme à l'état de l'art, que rate-t-elle, et quelles techniques éprouvées l'amélioreraient ?"

Your angle: **contrarian/limites — trous de config, placeholders et faux négatifs du statique** — Attaque le point faible de la méthode : ce qu'une détection de placeholders et une simulation statique ratent structurellement (état, réseau, permissions, ordre, effets de bord).
Search query: `detecting placeholder values missing configuration secrets in infrastructure code linters checkov gitleaks false negatives limits of static validation vs runtime execution`

## Task
Use WebSearch with the query above (or a refined version). Return the top 4-6 most relevant results.
Rank by relevance to the ORIGINAL question

[assistant] I'll search for research on the limits of static validation for detecting placeholders and configuration gaps.

[assistant] Let me search more specifically on config-scanner false negatives and dry-run limits.

[assistant] One more pair of searches on dry-run limits and multi-environment reproducibility.