[user] ## Adversarial Claim Verifier (voter 2/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quels sont les risques réels et les pratiques de durcissement d'un serveur LLM auto-hébergé (LM Studio, Ollama, llama.cpp, vLLM) qui écoute sur 0.0.0.0 sans authentification sur un réseau local ? Documenter : incidents et campagnes de scan constatés, capacités d'un attaquant ayant accès à l'endpoint OpenAI-compatible (exfiltration de prompts, abus de calcul, empoisonnement, pivot), et les parades éprouvées (bind loopback + relais authentifié, reverse proxy, mTLS, segmentation, allowlist). Contexte : LM Studio écoute en 0.0.0.0:1234 sur une machine qui porte aussi la base de données et les agents, sur un LAN domestique avec plusieurs nœuds légitimes qui doivent continuer d'y accéder. Question centrale : quelle parade offre le meilleur rapport sécurité/rupture de service ?

## Claim under review
"La parade recommandée est explicitement en quatre points, l'authentification du service et le retrait de l'exposition réseau venant en premier — ce qui soutient une architecture bind loopback + relais authentifié plutôt qu'un simple filtrage réseau ; les endpoints d'énumération de modèles non protégés exposent en outre des clés API upstream vivantes et facturables (OpenAI, Anthropic, Google)."

**Source:** https://intezer.com/blog/how-attackers-access-llm-inference/ (primary)
**Supporting quote:** "The operator is still responsible for the basics: authentic

[assistant] I'll verify this claim by examining the source and searching for contradicting evidence.

[assistant] Two targeted extractions from the primary source confirm the shape of the problem.

**What holds up:**
- The four-point recommendation exists verbatim, dated 3 June 2026, Nicole Fishbein (Intezer) with Eran Segal (Kodem) — recent, credible vendor research, not marketing fluff.
- Unprotected model-list endpoints on LLM gateway proxies are documented: "None had protection on the model list endpoint. One host exposed 35 models across multiple providers", spanning OpenAI, Anthropic, Google, Groq, Cohere.

**What breaks the claim:**

1. **The load-bearing architectural inference is absent from the source.** The claim says the four points "soutient une architecture bind loopback + relais authentifié plutôt qu'un simple filtrage réseau". The article never makes that comparison. A targeted term sweep found **zero** occurrences of firewall, allowlist, VLAN, segmentation, VPN, reverse proxy, or mTLS. The only loopback/bind mentions are descriptive of defaults ("By default, it binds to 127.0.0.1", "setting OLLAMA_HOST=0.0.0.0 is a common step when accessing it from another machine") — factual observations about tool behaviour, not a recommendation ranking two defence architectures. The claim manufactures an arbitrage the source declines to make.

2. **Scope mismatch: public internet ≠ LAN.** The second point is "keep it off the **public internet** unless there is a reason to expose it". The research question concerns a home LAN with legitimate peer nodes. The article does not systematic