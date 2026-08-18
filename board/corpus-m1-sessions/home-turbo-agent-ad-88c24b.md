[user] ## Adversarial Claim Verifier (voter 2/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
État de l'art des « Agent Skills » (format SKILL.md avec frontmatter name/description, chargement progressif dans le contexte) : origine et spécification du format chez Anthropic, adoption réelle par l'écosystème (marketplaces type skillsmp.com, dépôts GitHub, compatibilité Claude Code / Codex CLI / ChatGPT), comparaison technique et fonctionnelle avec MCP (Model Context Protocol), les plugins Claude Code et les subagents — quand utiliser l'un plutôt que l'autre, bonnes pratiques de rédaction d'un skill (déclencheurs par mots-clés dans la description, taille, structure, scripts associés), et risques de sécurité liés à l'installation de skills tiers (injection de prompt, exécution de code, chaîne d'approvisionnement).

## Claim under review
"Anthropic identifie explicitement le risque d'approvisionnement lié aux skills tiers et recommande de n'installer que depuis des sources de confiance, d'auditer les skills moins fiables, et de surveiller les dépendances de code, les ressources embarquées et les instructions poussant Claude vers des sources réseau externes non fiables."

**Source:** https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills (primary)
**Supporting quote:** "Installing skills only from trusted sources. When installing a skill from a less-trusted source, thoroughly audit it before use."

## Checklis

[assistant] The primary source fetch confirms the quote nearly verbatim. Let me check whether Anthropic's current documentation still carries this guidance (currency check) and whether anyone disputes it.

[assistant] I verified the claim against the primary source and cross-checked for contradicting evidence.

**Verification results:**

1. **Quote → claim mapping**: The WebFetch of the Anthropic engineering post returns a dedicated security section that supports each element of the claim near-verbatim:
   - "We recommend installing skills only from trusted sources. When installing a skill from a less-trusted source, thoroughly audit it before use." → trusted sources + auditing less-trusted skills ✓
   - "Start by reading the contents of the files bundled in the skill... paying particular attention to **code dependencies and bundled resources like images or scripts**." → code dependencies + embedded resources ✓
   - "pay attention to **instructions or code within the skill that instruct Claude to connect to potentially untrusted external network sources**." → instructions pushing Claude toward untrusted external network sources ✓
   - "malicious skills may introduce vulnerabilities in the environment where they're used or direct Claude to exfiltrate data and take unintended actions." → explicit risk identification ✓

2. **Independent corroboration**: WebSearch returned a separate summary independently quoting the same Anthropic wording ("install only from trusted sources", "thoroughly audit untrusted skills", "exfiltrate data and take unintended actions"), so the fetch is not a single-source artifact.

3. **No contradiction found**: Third-party work (arXiv 2601.10338 empirical study of 31,