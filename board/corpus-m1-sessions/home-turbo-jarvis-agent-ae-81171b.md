[user] ## Adversarial Claim Verifier (voter 1/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quelles sont, en 2026, les ressources les plus utilisées et les plus utiles pour outiller Claude Code et les agents de codage IA : catalogues de skills (skillsmp, awesome-claude-*, marketplaces), dépôts de sous-agents, serveurs MCP, patterns de slash commands, hooks. Pour chaque catégorie : qui l'utilise réellement, quelle traction mesurable (stars, téléchargements, adoption documentée), quelles limites connues. Contexte du demandeur : il exploite déjà un corpus local de 268 895 recettes extraites de 1 013 dépôts, 30 072 fiches de skills, 511 CLI et 319 agents. Ce qui l'intéresse n'est pas la liste des ressources mais CE QUI MANQUE dans un écosystème qui a déjà tout ça.

## Claim under review
"Le registre MCP officiel est délibérément non-opinionné : il n'héberge que des métadonnées et délègue explicitement la curation et les notes communautaires aux agrégateurs en aval. Aucun classement ni score de qualité n'existe au niveau du registre."

**Source:** https://modelcontextprotocol.io/registry/about (primary)
**Supporting quote:** "The metadata hosted by the MCP Registry is deliberately unopinionated. Downstream aggregators can provide curation or additional metadata such as community ratings."

## Checklist
1. Is the claim actually supported by the quote, or is it an overreach/misread?
2. WebSearch for contradicting evidence — does any credible so

[assistant] Primary source fetched. Let me check the aggregators guide for any registry-level ranking signals that would qualify the claim.

[assistant] Two primary pages verified. I could not run WebSearch (session budget exhausted at 200/200), so the adversarial pass relies on primary-source cross-checking rather than third-party contradiction hunting.

**Attempted refutations and why they fail:**

1. *Overreach on "delegates"?* No — the word is literal. Beyond the cited quote, the same page's Trust and Security section states: "The MCP Registry **delegates** security scanning to: ... **Downstream aggregators** — MCP Registry aggregators and marketplaces can implement additional security checks, ratings, or curation."

2. *Does the registry secretly rank?* Checked the aggregators guide and the live API surface. `GET /v0.1/servers` supports only `limit`, `cursor`, and `updated_since` — no popularity sort, no download counts, no score field. Ratings and download counts appear only as an *example of what a subregistry injects* under `_meta` (`"com.example.subregistry/custom": {"user_rating": 4.5, "download_count": 12345}`), confirming they are downstream, not registry-native.

3. *Best counter-argument — the registry is not entirely signal-free.* It does operate namespace authentication (reverse-DNS / GitHub / HTTP challenge), a moderation policy with manual takedown, and a mutable `status` field (`deprecated` / `deleted`, where deleted "suggests the server might be spam, malware, or illegal"). This qualifies "non-opinionated" in the broad sense — but it is authenticity and abuse moderation, **not** ranking or quality scoring.