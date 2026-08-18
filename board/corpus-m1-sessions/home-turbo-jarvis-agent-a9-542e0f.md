[user] ## Adversarial Claim Verifier (voter 1/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Comment les systèmes multi-agents en production pondèrent, routent et arbitrent entre agents en 2026 ? Techniques documentées : routage par score, vote pondéré, consensus, cascade de repli, sélection d'outils par embedding, bandits/apprentissage du routage. Pour chacune : preuves d'efficacité, coûts, modes de défaillance connus. Contexte : un routeur local pondère par popularité 0,3 + reproductibilité 0,5 + sûreté 0,2 pour choisir parmi 268 895 recettes réparties en 9 familles, avec 319 agents enregistrés. Question centrale : quelles pondérations et quels mécanismes d'arbitrage ont fait leurs preuves, et lesquels échouent silencieusement à l'échelle ?

## Claim under review
"Un scoreur de pondération non contextuel (biais seul, sans caractéristiques par requête) dégénère en politique mono-modèle codée en dur : le routeur sélectionne toujours DeepSeek-chat. C'est le mode de défaillance silencieuse direct d'une pondération par popularité globale sans signal par requête."

**Source:** https://arxiv.org/pdf/2605.30736 (primary)
**Supporting quote:** "Replacing the embedding-augmented scorer with a bias-only non-contextual ridge model, which has no request-level features and learns only global arm preferences, collapses the router to always selecting DeepSeek-chat. This is mathematically equivalent to a hard-coded single-model policy."

## Checklist
1.

[assistant] I'll verify this claim about non-contextual scorers collapsing to single-model policies.

[assistant] The quote is verbatim. Let me read the full surrounding context to assess whether the claim overreaches.

[assistant] Verified the source directly. The quote is verbatim, but the surrounding context materially undercuts the claim's framing.

**Source confirmed:** arXiv 2605.30736 = "OrcaRouter: A Production-Oriented LLM Router with Hybrid Offline-Online Learning" (Bao, Tian, Zhang, Chen, Ma, Shi), submitted 29 May 2026. Extracted text: `/tmp/claude-1000/-home-turbo-jarvis/f503a673-a340-4712-8abd-b933e4d372b3/scratchpad/orca.txt`, quote at lines 345-349.

**What holds:** sentence 1 is a literal, verbatim match, and the mechanism is a mathematical tautology (a scorer with no per-request features has a constant per-arm score, so `argmax` is constant by construction). Not refutable.

**What fails — the "silent failure" gloss:**

1. **The paper contradicts "silent."** Same paragraph, titled *"Pick diversity"*, opens: *"A common concern in cost-aware routing is collapse to a single cheap model."* Line 154 notes LinTS variants *"mitigate single-arm collapse when bandit feedback is sparse."* Collapse is a named, expected, routinely-monitored concern — and 100% of traffic on one arm is the single most observable state a router can be in, detectable by a one-line histogram. This is the loudest failure mode, not a silent one.

2. **The paper's own numbers show it's barely a failure.** Line 237: the Always-DSC constant baseline gets **70.27% accuracy, $0.10/1K queries, S=70.31**. The deployed contextual router gets **75.54% at $1.00/1K, S=72.08**. The "degenerate" policy is 1.77 Arena points worse and *