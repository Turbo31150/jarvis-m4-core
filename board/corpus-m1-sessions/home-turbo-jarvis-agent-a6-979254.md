[user] ## Adversarial Claim Verifier (voter 2/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Comment les systèmes multi-agents en production pondèrent, routent et arbitrent entre agents en 2026 ? Techniques documentées : routage par score, vote pondéré, consensus, cascade de repli, sélection d'outils par embedding, bandits/apprentissage du routage. Pour chacune : preuves d'efficacité, coûts, modes de défaillance connus. Contexte : un routeur local pondère par popularité 0,3 + reproductibilité 0,5 + sûreté 0,2 pour choisir parmi 268 895 recettes réparties en 9 familles, avec 319 agents enregistrés. Question centrale : quelles pondérations et quels mécanismes d'arbitrage ont fait leurs preuves, et lesquels échouent silencieusement à l'échelle ?

## Claim under review
"Un repli naïf à intervalle fixe dans une flotte d'agents produit une synchronisation en troupeau : 100 agents ayant subi la même panne transitoire replanifient leur retry au même instant, saturent la limite de débit du fournisseur à chaque fenêtre et font rejeter la majorité des requêtes (dépense API incontrôlée)."

**Source:** https://arxiv.org/html/2607.17525 (primary)
**Supporting quote:** "all 100 agents encountered the transient failure simultaneously. Because the default retry logic used a fixed interval (e.g., 1 second), all 100 agents scheduled their retries at the exact same moment."

## Checklist
1. Is the claim actually supported by the quote, or is it an overreach/

[assistant] WebFetch confirmed via a small model — I must verify independently since that model can confabulate on 404 pages.

[assistant] Paper exists (HTTP 200). Now let me check the actual full text rather than trusting the summarizer.

[assistant] Section 6.2 "The Failover Retry Storm (Thundering Herd)" exists. Let me read the actual section body.

[assistant] The quote is verbatim and in context. Now checking source quality and whether the paper self-qualifies this finding.

[assistant] Verification complete. Findings:

**Source is real and verified firsthand** — not via the summarizer. `curl` returned HTTP 200 (42 KB abs, 274 KB HTML). arXiv:2607.17525, soumis le 20 juil. 2026, cs.LG, « FailureAtlas: A Taxonomy of Failure Modes in Multi-Provider LLM Serving Infrastructure », Vishal Pandey & Gopal Singh. Texte intégral extrait localement dans `/tmp/claude-1000/-home-turbo-jarvis/f503a673-a340-4712-8abd-b933e4d372b3/scratchpad/full.txt`.

**La citation est verbatim et en contexte** (§6.2 « The Failover Retry Storm (Thundering Herd) », Layer: Governance/Cost, Detectability: Loud). Chaque clause de l'affirmation se retrouve dans le paragraphe source, sans extrapolation : 100 agents concurrents, panne simultanée, intervalle fixe 1 s → retries au même instant, « persistently saturated the provider's rate limit on every retry window, rejecting the majority of requests », « runaway API spend for zero successful task completions ».

**Réserves réelles mais non disqualifiantes** (le papier les avoue lui-même) : banc simulé (« mock LLM-provider gateway »), biais d'auto-sourçage explicite en §8 (« Our evaluation harness was specifically designed to stress-test... retry policies »), préprint non relu, et la « dépense incontrôlée » dépend d'une facturation des complétions partielles, non universelle. Mais le mécanisme n'est pas extraordinaire — le papier le qualifie lui-même de « textbook example », et backoff exponentiel + jitter est la parade canonique (AWS Brooker 201