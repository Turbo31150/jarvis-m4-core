[user] ## Adversarial Claim Verifier (voter 2/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quels sont les risques réels et les pratiques de durcissement d'un serveur LLM auto-hébergé (LM Studio, Ollama, llama.cpp, vLLM) qui écoute sur 0.0.0.0 sans authentification sur un réseau local ? Documenter : incidents et campagnes de scan constatés, capacités d'un attaquant ayant accès à l'endpoint OpenAI-compatible (exfiltration de prompts, abus de calcul, empoisonnement, pivot), et les parades éprouvées (bind loopback + relais authentifié, reverse proxy, mTLS, segmentation, allowlist). Contexte : LM Studio écoute en 0.0.0.0:1234 sur une machine qui porte aussi la base de données et les agents, sur un LAN domestique avec plusieurs nœuds légitimes qui doivent continuer d'y accéder. Question centrale : quelle parade offre le meilleur rapport sécurité/rupture de service ?

## Claim under review
"Les capacités d'attaque documentées sur un endpoint LLM non authentifié couvrent l'extraction de modèle par requêtage répété, le détournement de calcul gratuit, la génération de contenu interdit et l'empoisonnement par upload de modèle malveillant sur les serveurs dormants."

**Source:** https://blogs.cisco.com/security/detecting-exposed-llm-servers-shodan-case-study-on-ollama (primary)
**Supporting quote:** "Attackers can reconstruct model parameters by querying an exposed ML server repeatedly ... Open AI models can be exploited for free computation, leadi

[assistant] I'll verify this claim by examining the source and searching for contradicting evidence.

[assistant] I've verified the quote and hunted for contradicting evidence. Here is my assessment.