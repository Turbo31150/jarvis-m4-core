[user] ## Adversarial Claim Verifier (voter 1/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quels sont les risques réels et les pratiques de durcissement d'un serveur LLM auto-hébergé (LM Studio, Ollama, llama.cpp, vLLM) qui écoute sur 0.0.0.0 sans authentification sur un réseau local ? Documenter : incidents et campagnes de scan constatés, capacités d'un attaquant ayant accès à l'endpoint OpenAI-compatible (exfiltration de prompts, abus de calcul, empoisonnement, pivot), et les parades éprouvées (bind loopback + relais authentifié, reverse proxy, mTLS, segmentation, allowlist). Contexte : LM Studio écoute en 0.0.0.0:1234 sur une machine qui porte aussi la base de données et les agents, sur un LAN domestique avec plusieurs nœuds légitimes qui doivent continuer d'y accéder. Question centrale : quelle parade offre le meilleur rapport sécurité/rupture de service ?

## Claim under review
"Chez llama.cpp server, 59 % des hôtes scannés étaient confirmés ouverts (sans authentification), le taux le plus élevé du scan, et environ 37 % divulguaient l'état des jobs en temps réel, confirmant qu'ils servaient des utilisateurs réels au moment du scan (fuite de l'activité et des prompts en cours)."

**Source:** https://intezer.com/blog/how-attackers-access-llm-inference/ (primary)
**Supporting quote:** "59% were confirmed open, more than any other platform in the scan. … About 37% also leaked real-time job state, confirming the host was actively servin

[assistant] I'll verify this claim about llama.cpp scan statistics from the Intezer blog post.

[assistant] The quote is verbatim. Now I need to check the article's definition of "confirmed open" and whether job state actually leaks prompts.