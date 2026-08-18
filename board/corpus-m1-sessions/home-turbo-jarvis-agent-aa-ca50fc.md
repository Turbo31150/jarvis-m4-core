[user] ## Adversarial Claim Verifier (voter 2/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Comment les systèmes multi-agents en production pondèrent, routent et arbitrent entre agents en 2026 ? Techniques documentées : routage par score, vote pondéré, consensus, cascade de repli, sélection d'outils par embedding, bandits/apprentissage du routage. Pour chacune : preuves d'efficacité, coûts, modes de défaillance connus. Contexte : un routeur local pondère par popularité 0,3 + reproductibilité 0,5 + sûreté 0,2 pour choisir parmi 268 895 recettes réparties en 9 familles, avec 319 agents enregistrés. Question centrale : quelles pondérations et quels mécanismes d'arbitrage ont fait leurs preuves, et lesquels échouent silencieusement à l'échelle ?

## Claim under review
"Une part substantielle du « plafond d'insolvabilité » (requêtes qu'aucun agent/modèle ne résoudrait) est un artefact de mesure, pas une limite réelle : biais du juge favorisant la verbosité, troncature sous budget de génération fixe, et incompatibilités de format de sortie."

**Source:** https://arxiv.org/abs/2605.07395 (primary)
**Supporting quote:** "a substantial portion of reported unsolvability stems from evaluation artifacts: (i) systematic judge biases favoring verbosity over correctness, (ii) truncation under fixed generation budgets, and (iii) output format mismatches"

## Checklist
1. Is the claim actually supported by the quote, or is it an overreach/misread?
2. Web

[assistant] I'll verify this claim about "unsolvability ceiling" being a measurement artifact.

[assistant] WebSearch budget is exhausted. Let me verify independently via the arXiv API (raw XML, harder to misread than a rendered page).

[assistant] Paper is real and the quote is verbatim. Let me check for contradicting/qualifying literature and whether it's been replicated or disputed.

[assistant] Verification complete. Summary of what I found.

**Paper existence — verified hard.** Independently confirmed via arXiv's own export API (raw Atom XML, not the WebFetch summarizer): `arXiv:2605.07395`, "Unsolvability Ceiling in Multi-LLM Routing: An Empirical Study of Evaluation Artifacts", Saloni Garg & Amit Sagtani, `<published>2026-05-08T07:49:24Z</published>`, DOI `10.48550/arXiv.2605.07395`, DBLP `journals/corr/abs-2605-07395`, S2 CorpusId 288111039. No withdrawal/comment notice on the abs page.

**Quote fidelity — verbatim.** The supporting quote matches the abstract word for word, including the `(i)/(ii)/(iii)` enumeration.

**Claim vs. quote — faithful, not an overreach.** The French claim preserves the paper's own hedge ("une part substantielle" = "a substantial portion"); it does *not* assert that all unsolvability is artifactual. The rest of the abstract strengthens it further ("we reduce measured unsolvability across tasks", "existing routing headroom estimates are substantially inflated"), with methodological controls the abstract names explicitly (dual-judge validation, exact-match anchoring, random-feature and shuffled-label controls).

**Caveats that qualify but do not refute:** unrefereed preprint, venue `arXiv.org`, `citationCount: 1`; model pool limited to Gemma 4 + Llama 3.1 (no frontier tier), so "no model in the pool can solve" is relative to a weak pool; benchmarks largely legacy/saturated. Also a scope mismatch with the local context — the paper says n