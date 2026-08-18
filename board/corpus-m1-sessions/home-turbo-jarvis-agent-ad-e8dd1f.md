[user] ## Adversarial Claim Verifier (voter 2/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quels sont les risques réels et les pratiques de durcissement d'un serveur LLM auto-hébergé (LM Studio, Ollama, llama.cpp, vLLM) qui écoute sur 0.0.0.0 sans authentification sur un réseau local ? Documenter : incidents et campagnes de scan constatés, capacités d'un attaquant ayant accès à l'endpoint OpenAI-compatible (exfiltration de prompts, abus de calcul, empoisonnement, pivot), et les parades éprouvées (bind loopback + relais authentifié, reverse proxy, mTLS, segmentation, allowlist). Contexte : LM Studio écoute en 0.0.0.0:1234 sur une machine qui porte aussi la base de données et les agents, sur un LAN domestique avec plusieurs nœuds légitimes qui doivent continuer d'y accéder. Question centrale : quelle parade offre le meilleur rapport sécurité/rupture de service ?

## Claim under review
"La parade recommandée par les chercheurs est double et compatible avec un maintien de service : ne pas binder sur 0.0.0.0 mais sur l'IP d'une interface explicite du réseau local, et placer un proxy/couche d'autorisation devant le port du dashboard."

**Source:** https://www.oligo.security/blog/shadowray-2-0-attackers-turn-ai-against-itself-in-global-campaign-that-hijacks-ai-into-self-propagating-botnet (primary)
**Supporting quote:** "Don't bind on 0.0.0.0"

## Checklist
1. Is the claim actually supported by the quote, or is it an overreach/misread?
2. WebS

[assistant] I'll verify this claim by examining the source and searching for contradicting evidence.

[assistant] Both halves of the claim are verbatim-confirmed in the primary source — but the source is about the wrong software.