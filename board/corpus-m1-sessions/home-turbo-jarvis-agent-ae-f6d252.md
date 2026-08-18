[user] ## Adversarial Claim Verifier (voter 3/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quels sont les risques réels et les pratiques de durcissement d'un serveur LLM auto-hébergé (LM Studio, Ollama, llama.cpp, vLLM) qui écoute sur 0.0.0.0 sans authentification sur un réseau local ? Documenter : incidents et campagnes de scan constatés, capacités d'un attaquant ayant accès à l'endpoint OpenAI-compatible (exfiltration de prompts, abus de calcul, empoisonnement, pivot), et les parades éprouvées (bind loopback + relais authentifié, reverse proxy, mTLS, segmentation, allowlist). Contexte : LM Studio écoute en 0.0.0.0:1234 sur une machine qui porte aussi la base de données et les agents, sur un LAN domestique avec plusieurs nœuds légitimes qui doivent continuer d'y accéder. Question centrale : quelle parade offre le meilleur rapport sécurité/rupture de service ?

## Claim under review
"88,89 % des serveurs exposés respectent la structure de routes standard OpenAI (ex. v1/chat/completions), ce qui permet à un attaquant d'utiliser un outillage générique unique contre des backends hétérogènes (LM Studio, Ollama, llama.cpp, vLLM) sans adaptation."

**Source:** https://blogs.cisco.com/security/detecting-exposed-llm-servers-shodan-case-study-on-ollama (primary)
**Supporting quote:** "88.89% adhered to the standardized route structure used by OpenAI (e.g., v1/chat/completions)" enabling "malicious tooling capable of interacting with multiple LLM

[assistant] I'll verify this claim by examining the primary source and searching for contradicting evidence.

[assistant] The WebSearch budget is exhausted. Let me re-fetch the source with a targeted prompt to pin down the denominator of the 88.89% figure.