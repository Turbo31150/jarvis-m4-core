[user] ## Adversarial Claim Verifier (voter 1/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quels sont les risques réels et les pratiques de durcissement d'un serveur LLM auto-hébergé (LM Studio, Ollama, llama.cpp, vLLM) qui écoute sur 0.0.0.0 sans authentification sur un réseau local ? Documenter : incidents et campagnes de scan constatés, capacités d'un attaquant ayant accès à l'endpoint OpenAI-compatible (exfiltration de prompts, abus de calcul, empoisonnement, pivot), et les parades éprouvées (bind loopback + relais authentifié, reverse proxy, mTLS, segmentation, allowlist). Contexte : LM Studio écoute en 0.0.0.0:1234 sur une machine qui porte aussi la base de données et les agents, sur un LAN domestique avec plusieurs nœuds légitimes qui doivent continuer d'y accéder. Question centrale : quelle parade offre le meilleur rapport sécurité/rupture de service ?

## Claim under review
"L'exploitation des endpoints d'inférence ouverts est industrialisée et revendue : plus de 175 000 hôtes Ollama exposés documentés (SentinelOne Labs / Censys), chaînés en réseaux d'IA anonymes, avec vente d'accès par abonnement à un gateway LLM alimenté par des endpoints Ollama volés (Operation Bizarre Bazaar)."

**Source:** https://intezer.com/blog/how-attackers-access-llm-inference/ (primary)
**Supporting quote:** "SentinelOne Labs and Censys already published the definitive survey, documenting 175,000+ hosts chained into anonymous AI networks. … sells sub

[assistant] Search budget is exhausted. Let me use WebFetch directly on the primary and purported upstream sources.

[assistant] Both upstream primaries fetched directly and cross-checked against the secondary source's framing.