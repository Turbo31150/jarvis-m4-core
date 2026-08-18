[user] ## Adversarial Claim Verifier (voter 2/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quels sont les risques réels et les pratiques de durcissement d'un serveur LLM auto-hébergé (LM Studio, Ollama, llama.cpp, vLLM) qui écoute sur 0.0.0.0 sans authentification sur un réseau local ? Documenter : incidents et campagnes de scan constatés, capacités d'un attaquant ayant accès à l'endpoint OpenAI-compatible (exfiltration de prompts, abus de calcul, empoisonnement, pivot), et les parades éprouvées (bind loopback + relais authentifié, reverse proxy, mTLS, segmentation, allowlist). Contexte : LM Studio écoute en 0.0.0.0:1234 sur une machine qui porte aussi la base de données et les agents, sur un LAN domestique avec plusieurs nœuds légitimes qui doivent continuer d'y accéder. Question centrale : quelle parade offre le meilleur rapport sécurité/rupture de service ?

## Claim under review
"Les outils offensifs sont conçus « backend-agnostic » : l'attaquant se contente de repointer le backend modèle vers n'importe quel endpoint OpenAI-compatible gratuit et non authentifié — donc un LM Studio en 0.0.0.0:1234 est interchangeable avec Ollama comme cible d'abus de calcul."

**Source:** https://www.sysdig.com/blog/llmjacking-evolved-attackers-are-using-stolen-ai-compute-to-build-offensive-agentic-tools (primary)
**Supporting quote:** "backend-agnostic tool whose operator had simply repointed its model backend at the free, unauthenticated Ollama"

#

[assistant] WebSearch budget is exhausted for the session. Let me verify the technical premise directly via fetches.

[assistant] Verified against the primary source directly. Key finding: two fetches confirm the article discusses **Ollama only** — LM Studio, llama.cpp and vLLM are never mentioned, and the transport (OpenAI-compatible `/v1` vs Ollama's native `/api`) is never established.