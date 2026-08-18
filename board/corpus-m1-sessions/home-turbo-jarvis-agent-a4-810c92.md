[user] ## Adversarial Claim Verifier (voter 3/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Comment les systèmes multi-agents en production pondèrent, routent et arbitrent entre agents en 2026 ? Techniques documentées : routage par score, vote pondéré, consensus, cascade de repli, sélection d'outils par embedding, bandits/apprentissage du routage. Pour chacune : preuves d'efficacité, coûts, modes de défaillance connus. Contexte : un routeur local pondère par popularité 0,3 + reproductibilité 0,5 + sûreté 0,2 pour choisir parmi 268 895 recettes réparties en 9 familles, avec 319 agents enregistrés. Question centrale : quelles pondérations et quels mécanismes d'arbitrage ont fait leurs preuves, et lesquels échouent silencieusement à l'échelle ?

## Claim under review
"Les routeurs appris standards s'effondrent silencieusement en prédiction de la classe majoritaire (≈79 % du temps « le plus petit palier est optimal »), un mode de défaillance vérifié par contrôles à traits aléatoires et labels mélangés — le routeur semble performant alors qu'il n'apprend rien du signal."

**Source:** https://arxiv.org/abs/2605.07395 (primary)
**Supporting quote:** "standard routers collapse to majority-class prediction (~79% smallest-tier optimal), confirmed via random-feature and shuffled-label controls"

## Checklist
1. Is the claim actually supported by the quote, or is it an overreach/misread?
2. WebSearch for contradicting evidence — does any credible so

[assistant] I'll verify this claim about learned routers collapsing to majority-class prediction.

[assistant] The paper exists. Let me verify the exact abstract text independently rather than trusting a summarizer's confirmation.

[assistant] Verified the abstract verbatim through two independent paths (arXiv abs page and the arXiv export API, which returns raw metadata rather than a rendered page).