[user] ## Adversarial Claim Verifier (voter 2/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Comment les systèmes multi-agents en production pondèrent, routent et arbitrent entre agents en 2026 ? Techniques documentées : routage par score, vote pondéré, consensus, cascade de repli, sélection d'outils par embedding, bandits/apprentissage du routage. Pour chacune : preuves d'efficacité, coûts, modes de défaillance connus. Contexte : un routeur local pondère par popularité 0,3 + reproductibilité 0,5 + sûreté 0,2 pour choisir parmi 268 895 recettes réparties en 9 familles, avec 319 agents enregistrés. Question centrale : quelles pondérations et quels mécanismes d'arbitrage ont fait leurs preuves, et lesquels échouent silencieusement à l'échelle ?

## Claim under review
"La part de bruit varie fortement selon le domaine : 12 % [6,19] sur GSM8K (écart 3,3 %), 36 % [31,42] sur MATH-500 (écart 10 %), 13 % [10,17] sur GPQA-Diamond (écart 42,8 %) — donc une pondération calibrée sur un benchmark ne se transfère pas à une autre famille de tâches."

**Source:** https://arxiv.org/html/2607.03436 (primary)
**Supporting quote:** "GSM8K (arithmetic): Gap of 3.3%, with 12% [6,19] noise share ... MATH-500 (unsaturated math): Gap of 10%, with 36% [31,42] noise share ... GPQA-Diamond (non-math science): Gap of 42.8%, with 13% [10,17] noise share"

## Checklist
1. Is the claim actually supported by the quote, or is it an overreach/misread?
2. WebSearch for con

[assistant] I'll verify this claim by checking the source and searching for contradicting evidence.

[assistant] The paper exists and the numbers check out. Let me examine the paper's own framing and caveats more closely.

[assistant] Verification complete. The numbers transcribe faithfully, but the inference drawn from them is contradicted by the source's own data and framing.