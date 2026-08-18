[user] ## Adversarial Claim Verifier (voter 2/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Comment les systèmes multi-agents en production pondèrent, routent et arbitrent entre agents en 2026 ? Techniques documentées : routage par score, vote pondéré, consensus, cascade de repli, sélection d'outils par embedding, bandits/apprentissage du routage. Pour chacune : preuves d'efficacité, coûts, modes de défaillance connus. Contexte : un routeur local pondère par popularité 0,3 + reproductibilité 0,5 + sûreté 0,2 pour choisir parmi 268 895 recettes réparties en 9 familles, avec 319 agents enregistrés. Question centrale : quelles pondérations et quels mécanismes d'arbitrage ont fait leurs preuves, et lesquels échouent silencieusement à l'échelle ?

## Claim under review
"Sans amorçage hors-ligne, les quatre variantes de bandit à information partielle (LinUCB vanilla 69,81 ; LinTS 70,00 ; ε-greedy 70,71 ; RR+UCB 70,74) font toutes moins bien ou à peine mieux que la meilleure politique constante Always-DSC (70,31) sur 8 400 requêtes : l'apprentissage du routage ne bat pas un choix fixe tant qu'il démarre à froid."

**Source:** https://arxiv.org/pdf/2605.30736 (primary)
**Supporting quote:** "Vanilla LinUCB (α=1) 69.81 ± 0.40 ... LinTS (v=0.3) 70.00 ± 0.42 ... ε-greedy LinUCB 70.71 ± 0.25 ... RR+UCB 70.74 ± 0.08 ... Always-DSC 70.31"

## Checklist
1. Is the claim actually supported by the quote, or is it an overreach/misread?
2. WebSearch for con

[assistant] Numbers match exactly. Now let me read the surrounding context to check what the table actually measures.

[assistant] I verified the numbers directly against the primary PDF rather than trusting the quote.

**Verification (all verbatim from the extracted PDF, Table 1, page 4):**

| Strategy | Arena S | Top arm % | # arms |
|---|---|---|---|
| Always-DSC | 70.31 | 100% | 1 |
| Vanilla LinUCB (α=1) | 69.81 ± 0.40 | 15.5% | 10 |
| LinTS (v=0.3) | 70.00 ± 0.42 | 72.8% | ≈2 |
| ε-greedy LinUCB | 70.71 ± 0.25 | 20.0% | 10 |
| RR+UCB | 70.74 ± 0.08 | 18.2% | 10 |
| Submission (warm-started) | 72.08 | 19.7% | 10 |
| Oracle | 80.72 | 39.4% | 10 |

Every figure in the claim matches exactly. The three load-bearing qualifiers are also verbatim in the paper: *"The four partial-information variants start without offline warmup (A_a,0=λI, b_a,0=0)"* and *"under-exploration in the cold-start partial-information regime"* (line 243–248), and *"All scores in the table are evaluated on the full RouterArena evaluation set of 8,400 prompts"* (line 226).

Extracted text: `/tmp/claude-1000/-home-turbo-jarvis/f503a673-a340-4712-8abd-b933e4d372b3/scratchpad/orca.txt`

**Attempted refutations that failed:** the paper is real (OrcaRouter, arXiv 2605.30736, 29 May 2026), it is primary, it is 2 months old, the cold-start framing is the authors' own words not the claimant's gloss, and the contrast case (warm-started submission at 72.08) is in the same table — so the "offline warm-start is what makes it work" reading is the paper's own thesis, not an outside inference.

**Caveats that don't reach refutation:** (1) two of f