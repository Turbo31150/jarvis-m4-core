[user] ## Adversarial Claim Verifier (voter 3/3)

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

[assistant] I fetched the primary source directly and verified both halves of the claim against it.

**Verification result:**

The Oligo ShadowRay 2.0 article (published 18 Nov 2025) contains both elements verbatim:
- "Don't bind on 0.0.0.0 to make your life easy" → "use an IP of an explicit network interface, such as the IP that is in the subnet of your local network or a trusted private VPC/VPN"
- "If you do need Ray's dashboard to be accessible, implement a proxy that adds an authorization layer to the Ray API when exposing it over the network"

The claim restates these accurately — it is not a misread or an overreach on the quote.

**Substantive caveats found (which qualify, but do not refute, the claim):**

1. **Scope transfer** — the source concerns **Ray** (AI compute framework, dashboard port 8265), not LM Studio / Ollama / llama.cpp / vLLM. The single quote fragment supplied ("Don't bind on 0.0.0.0") is thin; the full sentence is what actually carries the claim.
2. **Vendor context** — Oligo Security sells runtime security tooling, and the same recommendation list ends with "deploy runtime security tools." The binding advice itself is not a product pitch, and ShadowRay is a real, independently reported campaign, so this is credible primary research rather than marketing fluff.
3. **Technical limitation for the stated context** — on a host with a single LAN NIC, binding to `192.168.1.85` instead of `0.0.0.0` yields essentially identical exposure to the LAN. The measure only remov