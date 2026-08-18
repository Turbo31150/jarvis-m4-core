[user] ## Adversarial Claim Verifier (voter 3/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Comment les systèmes multi-agents en production pondèrent, routent et arbitrent entre agents en 2026 ? Techniques documentées : routage par score, vote pondéré, consensus, cascade de repli, sélection d'outils par embedding, bandits/apprentissage du routage. Pour chacune : preuves d'efficacité, coûts, modes de défaillance connus. Contexte : un routeur local pondère par popularité 0,3 + reproductibilité 0,5 + sûreté 0,2 pour choisir parmi 268 895 recettes réparties en 9 familles, avec 319 agents enregistrés. Question centrale : quelles pondérations et quels mécanismes d'arbitrage ont fait leurs preuves, et lesquels échouent silencieusement à l'échelle ?

## Claim under review
"Le bruit se concentre dans le régime de support mince : sur les 28–52 % de requêtes où ≤3 modèles sur 11 réussissent, le bruit représente 18–43 % de l'écart — c'est exactement là qu'un arbitrage par score échoue silencieusement, en attribuant à un « spécialiste » ce qui est un tirage chanceux."

**Source:** https://arxiv.org/html/2607.03436 (primary)
**Supporting quote:** "on the 28–52% of queries where ≤3 of 11 models are correct, noise comprises 18–43% of the gap"

## Checklist
1. Is the claim actually supported by the quote, or is it an overreach/misread?
2. WebSearch for contradicting evidence — does any credible source dispute or heavily qualify this?
3. Is the source qua

[assistant] The paper exists. Let me verify the exact numbers and the direction of the paper's conclusion.

[assistant] Two of three benchmarks were kept, one dropped. Let me confirm the definition of "noise" and the stratum definition.

[assistant] Verification complete. Multiple independent refutation grounds found — including from the cited source itself.

**Findings:**

1. **Cherry-picked range.** Table V covers three benchmarks: GSM8K (3% thin-support, 17% noise), MATH-500 (28%, 43%), GPQA-Diamond (52%, 18%). The claim's "28–52%" is produced by silently dropping GSM8K — 1 of only 3 benchmarks. The true range is **3–52%**, and noise is **17–43%**, not 18–43%.

2. **The "supporting quote" is not in the paper.** Two separate fetches confirm the string does not appear; it is a synthesized composite of Table V cells presented as verbatim.

3. **The interpretation is inverted.** Abstract: *"12–36% of the reported router-to-oracle gap is single-draw label noise… while the majority is genuine, recoverable specialist advantage."* Even inside thin-support strata, 57–83% of the gap is **real** specialist advantage. The paper argues scoring mostly *works* there.

4. **The mechanism is non-monotone.** GPQA has the *highest* thin-support share (52%) but the *lowest* noise share (18%); GSM8K the lowest (3%) with 17%. Only MATH-500 shows the strong effect. "Noise concentrates in thin support" is not supported as a rule across n=3.

5. **Concept substitution.** "Noise" = Δ = O^exp − O^repro, inflation of the *oracle upper bound* from stochastic decoding at T>0 — a measurement artifact in the benchmark ceiling, not a router mistaking a lucky draw for a specialist. Authors call the localization *"prospective, conservative,"* not an au