[user] ## Adversarial Claim Verifier (voter 1/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quels sont les risques réels et les pratiques de durcissement d'un serveur LLM auto-hébergé (LM Studio, Ollama, llama.cpp, vLLM) qui écoute sur 0.0.0.0 sans authentification sur un réseau local ? Documenter : incidents et campagnes de scan constatés, capacités d'un attaquant ayant accès à l'endpoint OpenAI-compatible (exfiltration de prompts, abus de calcul, empoisonnement, pivot), et les parades éprouvées (bind loopback + relais authentifié, reverse proxy, mTLS, segmentation, allowlist). Contexte : LM Studio écoute en 0.0.0.0:1234 sur une machine qui porte aussi la base de données et les agents, sur un LAN domestique avec plusieurs nœuds légitimes qui doivent continuer d'y accéder. Question centrale : quelle parade offre le meilleur rapport sécurité/rupture de service ?

## Claim under review
"Changing the listening port is not a defence: over 25 % of exposed Ollama instances were found on non-default ports (443, 80, 8080, 11435, 11439, 6399, 31816…), and Censys scans all 65 535 TCP ports, so "security through obscurity" fails against full-range scanners."

**Source:** https://censys.com/blog/ollama-drama-investigating-the-prevalence-of-ollama-open-instances-with-censys/ (primary)
**Supporting quote:** "Since Censys scans all 65,535 TCP ports, we also find over 25% of Ollama instances that are not on the default port, highlighting the importance 

[assistant] I'll verify this claim against the primary source and look for contradicting evidence.

[assistant] The primary source blocks WebFetch. Let me try an archive mirror and search for the exact figure.

[assistant] Exact quote confirmed. Now let me check whether the load-bearing "scans all 65,535 ports" element holds up, and look for contradicting sources.

[assistant] Let me verify the article's date, the port breakdown nuance, and search for methodology disputes.