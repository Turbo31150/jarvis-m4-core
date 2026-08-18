[user] ## Adversarial Claim Verifier (voter 3/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quels sont les risques réels et les pratiques de durcissement d'un serveur LLM auto-hébergé (LM Studio, Ollama, llama.cpp, vLLM) qui écoute sur 0.0.0.0 sans authentification sur un réseau local ? Documenter : incidents et campagnes de scan constatés, capacités d'un attaquant ayant accès à l'endpoint OpenAI-compatible (exfiltration de prompts, abus de calcul, empoisonnement, pivot), et les parades éprouvées (bind loopback + relais authentifié, reverse proxy, mTLS, segmentation, allowlist). Contexte : LM Studio écoute en 0.0.0.0:1234 sur une machine qui porte aussi la base de données et les agents, sur un LAN domestique avec plusieurs nœuds légitimes qui doivent continuer d'y accéder. Question centrale : quelle parade offre le meilleur rapport sécurité/rupture de service ?

## Claim under review
"48 % des hôtes observés annoncent des capacités de tool-calling, ce qui transforme l'endpoint non authentifié en vecteur d'exécution d'opérations privilégiées et de pivot vers d'autres systèmes — risque aggravé quand la même machine porte base de données et agents."

**Source:** https://www.sentinelone.com/labs/silent-brothers-ollama-hosts-form-anonymous-ai-network-beyond-platform-guardrails/ (primary)
**Supporting quote:** "48% of observed hosts advertise tool-calling capabilities"

## Checklist
1. Is the claim actually supported by the quote, or is it an 

[assistant] Let me check critical commentary and the technical mechanics of Ollama tool-calling.

[assistant] I have enough to rule. Let me consolidate the verification.

**Statistic itself: verified.** SentinelLABS + Censys, published 2026-01-29, "Over 48% of observed hosts advertise tool-calling capabilities via their API endpoints." Methodology is solid: 175,108 unique hosts, 7.23M observations, 293 days, 130 countries. The number is not the problem.

**The inference attached to it: refuted.** Three independent failures.