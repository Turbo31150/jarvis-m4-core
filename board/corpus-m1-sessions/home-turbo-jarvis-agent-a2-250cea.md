[user] ## Adversarial Claim Verifier (voter 3/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quelles sont, en 2026, les ressources les plus utilisées et les plus utiles pour outiller Claude Code et les agents de codage IA : catalogues de skills (skillsmp, awesome-claude-*, marketplaces), dépôts de sous-agents, serveurs MCP, patterns de slash commands, hooks. Pour chaque catégorie : qui l'utilise réellement, quelle traction mesurable (stars, téléchargements, adoption documentée), quelles limites connues. Contexte du demandeur : il exploite déjà un corpus local de 268 895 recettes extraites de 1 013 dépôts, 30 072 fiches de skills, 511 CLI et 319 agents. Ce qui l'intéresse n'est pas la liste des ressources mais CE QUI MANQUE dans un écosystème qui a déjà tout ça.

## Claim under review
"L'absence de vérification de propriété permet le détournement de serveurs référencés : 212 comptes GitHub redevenus réenregistrables (15,37 % des 1 379 liens invalides) et 304 comptes redirigés (renommés) récupérables par un tiers, dont 139 cas où de nouveaux serveurs existent déjà sous le compte renommé."

**Source:** https://arxiv.org/html/2510.16558 (primary)
**Supporting quote:** "Maintainer Hijacking (R3): 212 re-registrable accounts (15.37% of 1,379 invalid links) ... Redirection Hijacking (R4): 304 redirected accounts vulnerable to reclamation ... 139 cases where new servers exist under renamed accounts"

## Checklist
1. Is the claim actually supporte

[assistant] Let me verify the numbers weren't echoed back from my own prompt, using a neutral query.

[assistant] Verified against the primary source with two independent extraction passes.

**Checklist results:**

1. **Supported by quote?** Yes, and confirmed with a neutral prompt that supplied none of the claim's numbers. The paper's Table IV breaks down per registry: maintainer hijacking 111 (mcp.so) + 95 (MCP Market) + 5 (MCP Store) + 1 (Pulse MCP) = **212** ✓; redirection hijacking 98 + 50 + 155 + 1 = **304** ✓. The 1,379 denominator is arithmetically consistent (212 / 0.1537 = 1379.3) ✓. The "139 cases" figure is confirmed independently.

2. **Contradicting evidence?** Could not run WebSearch — session budget exhausted (200/200). This is a genuine gap in the adversarial protocol, noted below.

3. **Source quality vs. claim strength?** Exceeds requirement. Not a bare preprint: "A First Look at the Security Issues in the Model Context Protocol Ecosystem" (Xiaofan Li, Xing Gao, University of Delaware), **accepted to DSN 2026** — a top-tier peer-reviewed dependable-systems/security venue. Measurement study over 67,057 servers across six registries. This is the primary source, not a secondary report of it.

4. **Outdated?** No. Submitted Oct 2025, revised Apr 2026 — roughly three months old.

5. **Marketing/cherry-picked?** No. Academic measurement paper; the abstract states the general finding plainly: *"At the registry-level, weak vetting and ownership checks allow adversarial or hijacked servers to enter hosts."*

**Caveats that qualify but do not refute:** the figures are a point-in