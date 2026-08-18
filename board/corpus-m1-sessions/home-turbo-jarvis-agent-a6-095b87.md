[user] ## Adversarial Claim Verifier (voter 2/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quelles sont, en 2026, les ressources les plus utilisées et les plus utiles pour outiller Claude Code et les agents de codage IA : catalogues de skills (skillsmp, awesome-claude-*, marketplaces), dépôts de sous-agents, serveurs MCP, patterns de slash commands, hooks. Pour chaque catégorie : qui l'utilise réellement, quelle traction mesurable (stars, téléchargements, adoption documentée), quelles limites connues. Contexte du demandeur : il exploite déjà un corpus local de 268 895 recettes extraites de 1 013 dépôts, 30 072 fiches de skills, 511 CLI et 319 agents. Ce qui l'intéresse n'est pas la liste des ressources mais CE QUI MANQUE dans un écosystème qui a déjà tout ça.

## Claim under review
"Le catalogue de référence de l'écosystème (awesome-claude-code) ne suit réellement que 83 dépôts dans son ticker automatisé (data/repo-ticker.csv, 84 lignes dont l'en-tête), soit deux ordres de grandeur en dessous du corpus local du demandeur (1 013 dépôts). Le manque n'est pas la découverte : c'est que même la meilleure cartographie publique est un échantillon minuscule et non exhaustif."

**Source:** https://github.com/hesreallyhim/awesome-claude-code (primary)
**Supporting quote:** "full_name,stars,watchers,forks,stars_delta,watchers_delta,forks_delta,url … hesreallyhim/awesome-claude-code,51740,51740,4513,12,12,4"

## Checklist
1. Is the claim actually s

[assistant] Let me check whether `repo-ticker.csv` is actually the catalogue, or a separate artifact.

[assistant] The `data/` dir only holds the ticker. Let me find where the actual catalogue lives.