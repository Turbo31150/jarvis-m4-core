[user] ## Adversarial Claim Verifier (voter 1/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Comment les systèmes multi-agents en production pondèrent, routent et arbitrent entre agents en 2026 ? Techniques documentées : routage par score, vote pondéré, consensus, cascade de repli, sélection d'outils par embedding, bandits/apprentissage du routage. Pour chacune : preuves d'efficacité, coûts, modes de défaillance connus. Contexte : un routeur local pondère par popularité 0,3 + reproductibilité 0,5 + sûreté 0,2 pour choisir parmi 268 895 recettes réparties en 9 familles, avec 319 agents enregistrés. Question centrale : quelles pondérations et quels mécanismes d'arbitrage ont fait leurs preuves, et lesquels échouent silencieusement à l'échelle ?

## Claim under review
"Des routeurs appris hors ligne (RouterDC, GraphRouter) échouent silencieusement hors distribution : sur 3 tâches jamais vues, ils tombent à 44,55 % et 52,45 % de score moyen, soit NETTEMENT SOUS le simple repli « toujours le plus gros modèle » (64,50 %) — le routage devient alors pire que l'absence de routage, sans signal d'erreur."

**Source:** https://arxiv.org/pdf/2510.07429 (primary)
**Supporting quote:** "As shown in Table 3, the full-information routers (RouterDC and GraphRouter) struggle to generalize, with their performance dropping sharply on MBPP and HpQA. In contrast, BaRP demonstrates robust generalization, achieving the highest average score (66.08%) among all met

[assistant] Numbers verified verbatim. Now checking for contradicting evidence from RouterDC's own paper.

[assistant] Verification complete. I extracted Table 3 directly from the PDF and cross-checked against RouterDC's own paper.

**Numbers: verbatim exact.** Table 3 of arXiv 2510.07429 (Wang Wei et al., "Learning to Route LLMs from Bandit Feedback", 10 oct. 2025, marked *Preprint. Under Review*), p.6:

| Methods | MBPP | Hellaswag | HpQA | Avg |
|---|---|---|---|---|
| Smallest LLM | 34.43 | 25.48 | 27.49 | 29.14 |
| Largest LLM | 68.62 | 83.96 | 40.93 | **64.50** |
| RouterDC | 39.06 | 69.60 | 25.00 | **44.55** |
| GraphRouter | 64.29 | 70.87 | 22.20 | **52.45** |
| Ours (BaRP) | 68.24 | 83.72 | 46.29 | 66.08 |

**But three refutation vectors survive:**

1. **Contradicted by the primary source on RouterDC.** RouterDC's own paper (arXiv 2409.19886, NeurIPS 2024 — peer-reviewed, unlike 2510.07429) states in its abstract that RouterDC "largely outperforms individual top-performing LLMs as well as existing routing methods on both in-distribution (+2.76%) and out-of-distribution (+1.90%) tasks." That is the *opposite sign* on the exact axis the claim asserts. Two papers, opposite verdicts, and the one reporting failure is the one selling a competitor (BaRP). A ~30-point MBPP gap (39.06 vs 68.62) in a third-party reimplementation is a textbook undertuned-baseline signature.

2. **"Silencieusement / sans signal d'erreur" is fabricated.** The paper never discusses OOD detection, confidence signalling, or failure visibility — anywhere. §4.2 is a plain generalization benchmark. That clause, which i