[user] ## Adversarial Claim Verifier (voter 1/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quelles sont, en 2026, les ressources les plus utilisées et les plus utiles pour outiller Claude Code et les agents de codage IA : catalogues de skills (skillsmp, awesome-claude-*, marketplaces), dépôts de sous-agents, serveurs MCP, patterns de slash commands, hooks. Pour chaque catégorie : qui l'utilise réellement, quelle traction mesurable (stars, téléchargements, adoption documentée), quelles limites connues. Contexte du demandeur : il exploite déjà un corpus local de 268 895 recettes extraites de 1 013 dépôts, 30 072 fiches de skills, 511 CLI et 319 agents. Ce qui l'intéresse n'est pas la liste des ressources mais CE QUI MANQUE dans un écosystème qui a déjà tout ça.

## Claim under review
"Les écosystèmes ouverts de skills d'agents sont caractérisés, dans une étude arXiv 2026, comme redondants, de qualité inégale et sensibles à l'environnement — la masse d'artefacts n'est donc pas un actif net, et les mises à jour non filtrées polluent le contexte futur. C'est précisément la couche manquante pour un corpus déjà volumineux."

**Source:** https://arxiv.org/abs/2605.18401 (primary)
**Supporting quote:** "Yet open skill ecosystems contain redundant, uneven, environment-sensitive artifacts, and indiscriminate updates can pollute future context."

## Checklist
1. Is the claim actually supported by the quote, or is it an overreach/misread?
2. WebSear

[assistant] Verified the quote. Now checking whether the paper actually substantiates the characterization or merely asserts it as motivation.

[assistant] Verification complete. Full paper retrieved and text-extracted.

**Source check:** arXiv:2605.18401 exists and is exactly what is cited — *SkillsVote: Lifecycle Governance of Agent Skills from Collection, Recommendation to Evolution* (Liu, Yang, Jiang, Tang, Xiong, Luo, Li), submitted 18 May 2026, revised 14 June 2026. The supporting quote is **verbatim in the abstract**, not paraphrased or stitched.

**Is the characterization merely motivational rhetoric?** No — it is quantitatively backed in the paper's own profiling (Figure 9, Appendix A.1):

| Curation stage | Skills remaining |
|---|---|
| Collected from GitHub | 1 681 615 |
| After format validation | 794 617 |
| After content deduplication | 291 092 (−63 % of validated) |
| High-quality subset | 187 292 (11 % of raw) |

Quality/verifiability rubric pass rates (Figure 7): content consistency 98 %, task orientation 97 %, but **environment controllability 85 %, task constructability 70 %, reference completeness 67 %, success verifiability 64 %** — i.e. "uneven" and "environment-sensitive" are measured, not asserted. The paper also finds GitHub stars are *not* a usable proxy: "repository popularity … is not a reliable proxy for whether a skill is valid, distinct, or ready for execution."

**Does the paper's own data support "la masse d'artefacts n'est pas un actif net"?** Yes, and more strongly than the claim states: the *curated* open-source library **degrades** some agents — "improves Terminal-Bench 2.0 for GPT-5.2 and G