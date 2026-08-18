[user] ## Adversarial Claim Verifier (voter 3/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quels sont les risques réels et les pratiques de durcissement d'un serveur LLM auto-hébergé (LM Studio, Ollama, llama.cpp, vLLM) qui écoute sur 0.0.0.0 sans authentification sur un réseau local ? Documenter : incidents et campagnes de scan constatés, capacités d'un attaquant ayant accès à l'endpoint OpenAI-compatible (exfiltration de prompts, abus de calcul, empoisonnement, pivot), et les parades éprouvées (bind loopback + relais authentifié, reverse proxy, mTLS, segmentation, allowlist). Contexte : LM Studio écoute en 0.0.0.0:1234 sur une machine qui porte aussi la base de données et les agents, sur un LAN domestique avec plusieurs nœuds légitimes qui doivent continuer d'y accéder. Question centrale : quelle parade offre le meilleur rapport sécurité/rupture de service ?

## Claim under review
"Les parades recommandées par Talos combinent authentification applicative (clé API / OAuth2) et isolation réseau (pare-feu, security groups, sous-réseaux privés), plus une passerelle API pour le rate-limiting — le changement de port par défaut n'étant cité que comme mesure d'appoint, pas comme protection."

**Source:** https://blogs.cisco.com/security/detecting-exposed-llm-servers-shodan-case-study-on-ollama (primary)
**Supporting quote:** "Enforce API key or OAuth2-based authentication ... Use security groups, firewalls, and private subnets to isolate LLM 

[assistant] I'll verify this claim by examining the source and searching for contradicting evidence.

[assistant] Verification complete. I attempted three refutation angles (quote overreach, contradicting coverage, source quality/date) and all failed.