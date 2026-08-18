[user] ## Adversarial Claim Verifier (voter 2/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quelles sont, en 2026, les ressources les plus utilisées et les plus utiles pour outiller Claude Code et les agents de codage IA : catalogues de skills (skillsmp, awesome-claude-*, marketplaces), dépôts de sous-agents, serveurs MCP, patterns de slash commands, hooks. Pour chaque catégorie : qui l'utilise réellement, quelle traction mesurable (stars, téléchargements, adoption documentée), quelles limites connues. Contexte du demandeur : il exploite déjà un corpus local de 268 895 recettes extraites de 1 013 dépôts, 30 072 fiches de skills, 511 CLI et 319 agents. Ce qui l'intéresse n'est pas la liste des ressources mais CE QUI MANQUE dans un écosystème qui a déjà tout ça.

## Claim under review
"La modération est quasi inexistante par conception : les consommateurs doivent supposer une modération « minimale à nulle », et le registre reconnaît que du contenu théoriquement supprimable y subsiste — donc toute donnée scrapée depuis le registre est non fiable telle quelle."

**Source:** https://modelcontextprotocol.io/registry/about (primary)
**Supporting quote:** "The MCP Registry does not make guarantees about moderation, and consumers should assume minimal-to-no moderation. ... This means there may be content in the MCP Registry that should be removed under this policy, but which we haven't yet removed. Consumers should treat scraped data accordingly.

[assistant] The /about page doesn't contain the quoted text. Let me check the actual moderation policy page.

[assistant] I fetched both the cited URL and the actual policy page. Here's what I found.

**The cited URL does not contain the quote.** `https://modelcontextprotocol.io/registry/about` — fetched in full — contains no text about "minimal-to-no moderation" or "scraped data". Its Trust and Security section says the opposite in tone: it enumerates namespace authentication (reverse-DNS, GitHub/DNS/HTTP challenges), character limits + regex validation, delegated security scanning, and manual takedown. The quote is actually on a different page, `/registry/moderation-policy`.

**On that page the quote is verbatim accurate**, under a heading literally titled "Disclaimer":
> "The MCP Registry **does not** make guarantees about moderation, and consumers should assume minimal-to-no moderation. The MCP Registry is a community supported project, and we have limited active moderation capabilities. ... This means there may be content in the MCP Registry that should be removed under this policy, but which we haven't yet removed. Consumers should treat scraped data accordingly."

**But the same page contradicts "quasi inexistante" as a factual description.** There is a "What We Remove" section: illegal content, malware ("regardless of intentions"), spam (with three enumerated patterns), and non-functioning servers. Combined with `/about`'s Spam Prevention section, that is a real if thin moderation stack — not "quasi inexistante". The disclaimer is a *capacity* caveat ("limited active moderation capabilit