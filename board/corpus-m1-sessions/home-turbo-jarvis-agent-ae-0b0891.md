[user] ## Adversarial Claim Verifier (voter 2/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Comment les systèmes multi-agents en production pondèrent, routent et arbitrent entre agents en 2026 ? Techniques documentées : routage par score, vote pondéré, consensus, cascade de repli, sélection d'outils par embedding, bandits/apprentissage du routage. Pour chacune : preuves d'efficacité, coûts, modes de défaillance connus. Contexte : un routeur local pondère par popularité 0,3 + reproductibilité 0,5 + sûreté 0,2 pour choisir parmi 268 895 recettes réparties en 9 familles, avec 319 agents enregistrés. Question centrale : quelles pondérations et quels mécanismes d'arbitrage ont fait leurs preuves, et lesquels échouent silencieusement à l'échelle ?

## Claim under review
"Le vecteur de pondération n'a pas besoin d'être figé à la conception : conditionner la politique sur w = (w_q, w_c) échantillonné aléatoirement sur le 1-simplexe pendant l'entraînement permet de régler l'arbitrage au moment de l'inférence sans réentraînement, avec un effet monotone quantifié (coût moyen 0,074 $ à w_c=0,2 → 0,015 $ à w_c=0,8, score moyen déclinant progressivement, surtout sur NQ et MMLU)."

**Source:** https://arxiv.org/pdf/2510.07429 (primary)
**Supporting quote:** "The cost decreases steadily from $0.074 at wc = 0.2 to only $0.015 at wc = 0.8, with consistent reductions across all tasks. This demonstrates that the router effectively adapts its selections in l

[assistant] Web search budget exhausted. Let me fetch the PDF directly for the specific numbers.

[assistant] I read the actual PDF rather than relying on the summarizer. Every component of the claim is verbatim verifiable.

**Verification against the primary source** (`arXiv:2510.07429v1`, "Learning to Route LLMs from Bandit Feedback: One Policy, Many Trade-offs", Wang Wei, Tiankai Yang, Hongjie Chen, Yue Zhao, Franck Dernoncourt, Ryan A. Rossi, Hoda Eldardiry — 8 Oct 2025). Extracted text at `/tmp/claude-1000/-home-turbo-jarvis/f503a673-a340-4712-8abd-b933e4d372b3/scratchpad/barp.txt`:

- **1-simplex conditioning** (Sec 2.1): "wt = (wtq , wtc ) is a user preference vector on the 1-simplex."
- **Random sampling during training** (Sec 2.4): "to train a single policy that can serve diverse user preferences, we randomly sample the preference vector wt for each training instance (uniformly on the 1-simplex)." Algorithm 1 line 4: "sample preference wt (random on the 1-simplex)."
- **No retraining at inference** (Sec 4.4.1): "This allows the behavior of BaRP to be tuned to specific deployment requirements without any need for retraining."
- **Cost numbers**: verbatim as quoted.
- **Score decline incl. NQ/MMLU** (Sec 4.4.1): "as wc increases, the average score gradually declines, most noticeably on NQ and MMLU."

The reward is a linear scalarization: `rt ← wtq·qt − wtc·c̃t` with `c̃t = min(ct/τ, 1)`.

**Caveats that qualify but do not refute**: it is a v1 preprint marked "Preprint. Under Review" with no venue acceptance after ~10 months; results are author-self-reported with no independent