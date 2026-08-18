[user] ## Adversarial Claim Verifier (voter 1/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quels sont les risques réels et les pratiques de durcissement d'un serveur LLM auto-hébergé (LM Studio, Ollama, llama.cpp, vLLM) qui écoute sur 0.0.0.0 sans authentification sur un réseau local ? Documenter : incidents et campagnes de scan constatés, capacités d'un attaquant ayant accès à l'endpoint OpenAI-compatible (exfiltration de prompts, abus de calcul, empoisonnement, pivot), et les parades éprouvées (bind loopback + relais authentifié, reverse proxy, mTLS, segmentation, allowlist). Contexte : LM Studio écoute en 0.0.0.0:1234 sur une machine qui porte aussi la base de données et les agents, sur un LAN domestique avec plusieurs nœuds légitimes qui doivent continuer d'y accéder. Question centrale : quelle parade offre le meilleur rapport sécurité/rupture de service ?

## Claim under review
"Intezer a conduit un scan Internet actif d'environ 4 500 hôtes sur onze plateformes d'hébergement LLM — les serveurs d'inférence auto-hébergés sont donc une surface scannée systématiquement, pas une menace théorique."

**Source:** https://intezer.com/blog/how-attackers-access-llm-inference/ (primary)
**Supporting quote:** "We scanned roughly 4,500 hosts across eleven of them"

## Checklist
1. Is the claim actually supported by the quote, or is it an overreach/misread?
2. WebSearch for contradicting evidence — does any credible source dispute or heavily qual

[assistant] The quote is verbatim. Now let me check the antecedent of "eleven of them" and the scan methodology.

[assistant] Primary source verified verbatim, twice, with the pronoun antecedent resolved. WebSearch budget for this session was exhausted, so independent corroboration was not possible — I note that as a confidence limit.