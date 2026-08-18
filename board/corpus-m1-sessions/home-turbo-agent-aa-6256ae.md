[user] ## Adversarial Claim Verifier (voter 2/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
État de l'art des « Agent Skills » (format SKILL.md avec frontmatter name/description, chargement progressif dans le contexte) : origine et spécification du format chez Anthropic, adoption réelle par l'écosystème (marketplaces type skillsmp.com, dépôts GitHub, compatibilité Claude Code / Codex CLI / ChatGPT), comparaison technique et fonctionnelle avec MCP (Model Context Protocol), les plugins Claude Code et les subagents — quand utiliser l'un plutôt que l'autre, bonnes pratiques de rédaction d'un skill (déclencheurs par mots-clés dans la description, taille, structure, scripts associés), et risques de sécurité liés à l'installation de skills tiers (injection de prompt, exécution de code, chaîne d'approvisionnement).

## Claim under review
"Anthropic's decision rule between Skills and subagents is that Skills are portable capabilities loadable by any Claude instance ("training materials"), whereas subagents are self-contained agents that handle workflows independently."

**Source:** https://claude.com/blog/skills-explained (primary)
**Supporting quote:** "Use Skills when: You want capabilities that any Claude instance can load and use. Skills are like training materials...Use subagents when: You need complete, self-contained agents designed for specific purposes that handle workflows independently."

## Checklist
1. Is the claim actually supported

[assistant] The quote checks out verbatim. Now let me test whether the "portability" framing is the actual distinguishing criterion, or a simplification contradicted by Anthropic's own technical docs.

[assistant] Let me verify whether subagents are also portable/shareable files, which would break the claim's dichotomy.

[assistant] Verification complete. I found a substantive defect.

**What holds up:** The quote is verbatim accurate from the primary source. `claude.com/blog/skills-explained` (dated March 5, 2026 — current) does say "Use Skills when: You want capabilities that any Claude instance can load and use... Skills are like training materials" and "Use subagents when: You need complete, self-contained agents designed for specific purposes that handle workflows independently." Not fabricated, not outdated.

**What breaks it:** The claim elevates a marketing-blog analogy into "Anthropic's decision rule," and the discriminating axis it names — portability — does not discriminate. Anthropic's own primary technical documentation contradicts it.