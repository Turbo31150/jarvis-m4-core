[user] ## Adversarial Claim Verifier (voter 1/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quels sont les risques réels et les pratiques de durcissement d'un serveur LLM auto-hébergé (LM Studio, Ollama, llama.cpp, vLLM) qui écoute sur 0.0.0.0 sans authentification sur un réseau local ? Documenter : incidents et campagnes de scan constatés, capacités d'un attaquant ayant accès à l'endpoint OpenAI-compatible (exfiltration de prompts, abus de calcul, empoisonnement, pivot), et les parades éprouvées (bind loopback + relais authentifié, reverse proxy, mTLS, segmentation, allowlist). Contexte : LM Studio écoute en 0.0.0.0:1234 sur une machine qui porte aussi la base de données et les agents, sur un LAN domestique avec plusieurs nœuds légitimes qui doivent continuer d'y accéder. Question centrale : quelle parade offre le meilleur rapport sécurité/rupture de service ?

## Claim under review
"Un scan Shodan mené par Cisco Talos a identifié 1 139 instances Ollama exposées et non authentifiées sur Internet, dont plus de 1 000 détectées en 10 minutes — preuve que l'exposition d'un serveur LLM est découverte quasi instantanément par les scanners d'opportunité."

**Source:** https://blogs.cisco.com/security/detecting-exposed-llm-servers-shodan-case-study-on-ollama (primary)
**Supporting quote:** "we identified 1,139 vulnerable Ollama instances ... over 1,000 instances detected within the first 10 minutes"

## Checklist
1. Is the claim actually suppor

[assistant] I'll fetch the primary source and search for corroborating/contradicting evidence.

[assistant] The quote checks out verbatim. Now let me test the *inference* — what the "10 minutes" actually measures.

[assistant] Verification complete. The numbers are real; the inference attached to them is not.

**What holds up:** The quote is verbatim and correctly attributed. Cisco blog (Tziakouris & Biasiotto, 1 Sept 2025) does state 1,139 instances and ">1,000 within the first 10 minutes". Independently corroborated by The Register (2 Sept 2025) and Bank Info Security.

**What breaks:** The "10 minutes" measures Cisco's *own PoC tool enumerating Shodan's pre-existing index* — a two-stage pipeline (query Shodan banners for port 11434/"Ollama"/"uvicorn", then probe each endpoint). It is a harvest rate against servers *already indexed*, not a time-to-first-contact measurement on a newly exposed host. No honeypot, no fresh-exposure timing experiment exists in the study. The claim's conclusion — "preuve que l'exposition est découverte quasi instantanément par les scanners d'opportunité" — is a different proposition that this methodology cannot establish.

**Secondary inflation:** the claim says 1,139 were "exposées et non authentifiées". The source itself says only 214 (18.8%) were actively hosting live models; ~80% "did not have any models instantiated". The genuinely abusable set is 214, not 1,139.

**Relevance failure for the research question:** Shodan cannot index an RFC1918 LAN address. The study concerns Internet-exposed hosts (OLLAMA_HOST=0.0.0.0 with a routable IP); citing it as evidence of risk for LM Studio on 0.0.0.0:1234 behind domestic NAT is a category error.

Sources: [Cisco Blogs](htt