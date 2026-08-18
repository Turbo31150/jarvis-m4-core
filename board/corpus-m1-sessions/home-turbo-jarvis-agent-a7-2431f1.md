[user] ## Adversarial Claim Verifier (voter 1/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quels sont les risques réels et les pratiques de durcissement d'un serveur LLM auto-hébergé (LM Studio, Ollama, llama.cpp, vLLM) qui écoute sur 0.0.0.0 sans authentification sur un réseau local ? Documenter : incidents et campagnes de scan constatés, capacités d'un attaquant ayant accès à l'endpoint OpenAI-compatible (exfiltration de prompts, abus de calcul, empoisonnement, pivot), et les parades éprouvées (bind loopback + relais authentifié, reverse proxy, mTLS, segmentation, allowlist). Contexte : LM Studio écoute en 0.0.0.0:1234 sur une machine qui porte aussi la base de données et les agents, sur un LAN domestique avec plusieurs nœuds légitimes qui doivent continuer d'y accéder. Question centrale : quelle parade offre le meilleur rapport sécurité/rupture de service ?

## Claim under review
"Une infrastructure IA auto-hébergée exposée sans authentification est massivement scannée et exploitée à l'échelle mondiale : Oligo dénombre plus de 200 000 serveurs Ray exposés à Internet, dont une partie confirmée vulnérable ou déjà compromise (campagne ShadowRay 2.0, exploitant CVE-2023-48022)."

**Source:** https://www.oligo.security/blog/shadowray-2-0-attackers-turn-ai-against-itself-in-global-campaign-that-hijacks-ai-into-self-propagating-botnet (primary)
**Supporting quote:** "over 200,000 Ray servers remain exposed to the internet, with a portion co

[assistant] Web search budget is exhausted; I'll fetch corroborating/contradicting sources directly.

[assistant] Vérification faite : primaire (Oligo) + NVD + Anyscale + deux médias tier-1 indépendants.