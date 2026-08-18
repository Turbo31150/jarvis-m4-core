[user] ## Adversarial Claim Verifier (voter 1/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quels sont les risques réels et les pratiques de durcissement d'un serveur LLM auto-hébergé (LM Studio, Ollama, llama.cpp, vLLM) qui écoute sur 0.0.0.0 sans authentification sur un réseau local ? Documenter : incidents et campagnes de scan constatés, capacités d'un attaquant ayant accès à l'endpoint OpenAI-compatible (exfiltration de prompts, abus de calcul, empoisonnement, pivot), et les parades éprouvées (bind loopback + relais authentifié, reverse proxy, mTLS, segmentation, allowlist). Contexte : LM Studio écoute en 0.0.0.0:1234 sur une machine qui porte aussi la base de données et les agents, sur un LAN domestique avec plusieurs nœuds légitimes qui doivent continuer d'y accéder. Question centrale : quelle parade offre le meilleur rapport sécurité/rupture de service ?

## Claim under review
"Environ 175 000 instances Ollama sont exposées publiquement dans plus de 130 pays, ce qui démontre l'ampleur du scan opportuniste visant les endpoints LLM auto-hébergés non authentifiés."

**Source:** https://www.sysdig.com/blog/llmjacking-evolved-attackers-are-using-stolen-ai-compute-to-build-offensive-agentic-tools (primary)
**Supporting quote:** "roughly 175,000 publicly exposed Ollama instances across more than 130 countries"

## Checklist
1. Is the claim actually supported by the quote, or is it an overreach/misread?
2. WebSearch for contradicting evid

[assistant] Web search budget is exhausted. Let me fetch the underlying cited sources directly.

[assistant] I have enough to judge. Summary of what I found:

**The number traces to a real study, but the claim's inference and the source's corroboration both break down.**

1. **The quote is accurate** — Sysdig (17 juin 2026) does say "roughly 175,000 publicly exposed Ollama instances across more than 130 countries." It links to https://thehackernews.com/2026/01/researchers-find-175000-publicly.html (29 jan. 2026), which attributes the census to SentinelLABS + Censys. So the raw number is traceable.

2. **The "corroboration" is false by two orders of magnitude.** Sysdig writes the figure is "corroborated by Cisco's Shodan-based survey" and links https://blogs.cisco.com/security/detecting-exposed-llm-servers-shodan-case-study-on-ollama. That survey (1 sept. 2025) found **1,139 exposed Ollama servers**, of which only **214 (18.8%) actually hosted a model** — ~925 were empty installs. 1,139 vs 175,000 is a 154× gap. Cisco contradicts the order of magnitude rather than confirming it.

3. **The inference is a non-sequitur.** An exposure census counts *attack surface* (hosts answering on 11434), not *scanning campaigns*. Neither SentinelLABS/Censys nor Cisco measured opportunistic scan volume against LLM endpoints. "175k exposed ⇒ démontre l'ampleur du scan opportuniste" swaps surface for activity.

4. **"Non authentifiés" is not established.** THN's writeup gives no deduplication, honeypot-filtering, or auth-status breakdown; Cisco's data (80% with no model instantiated) suggests the genui