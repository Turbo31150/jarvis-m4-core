[user] ## Adversarial Claim Verifier (voter 2/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quels sont les risques réels et les pratiques de durcissement d'un serveur LLM auto-hébergé (LM Studio, Ollama, llama.cpp, vLLM) qui écoute sur 0.0.0.0 sans authentification sur un réseau local ? Documenter : incidents et campagnes de scan constatés, capacités d'un attaquant ayant accès à l'endpoint OpenAI-compatible (exfiltration de prompts, abus de calcul, empoisonnement, pivot), et les parades éprouvées (bind loopback + relais authentifié, reverse proxy, mTLS, segmentation, allowlist). Contexte : LM Studio écoute en 0.0.0.0:1234 sur une machine qui porte aussi la base de données et les agents, sur un LAN domestique avec plusieurs nœuds légitimes qui doivent continuer d'y accéder. Question centrale : quelle parade offre le meilleur rapport sécurité/rupture de service ?

## Claim under review
"L'exploitation des endpoints d'inférence ouverts est industrialisée et revendue : plus de 175 000 hôtes Ollama exposés documentés (SentinelOne Labs / Censys), chaînés en réseaux d'IA anonymes, avec vente d'accès par abonnement à un gateway LLM alimenté par des endpoints Ollama volés (Operation Bizarre Bazaar)."

**Source:** https://intezer.com/blog/how-attackers-access-llm-inference/ (primary)
**Supporting quote:** "SentinelOne Labs and Censys already published the definitive survey, documenting 175,000+ hosts chained into anonymous AI networks. … sells sub

[assistant] I'll verify this claim by checking the primary source and searching for corroborating or contradicting evidence.

[assistant] The intezer article does contain the quote. Now let me verify the underlying attributions — the SentinelOne/Censys survey and the Pillar Security report.

[assistant] The Bizarre Bazaar portion checks out. Now the critical part: the "175,000+ hosts / SentinelOne Labs + Censys" figure. Let me hunt for that primary source.

[assistant] The SentinelLABS report is real. Let me verify its actual findings and check whether the claim's characterization is accurate.

[assistant] I have enough to adjudicate. Let me record my verification.

**Verified independently (not just taking intezer's word):**

| Sub-claim | Status | Primary source |
|---|---|---|
| 175,000+ exposed Ollama hosts, SentinelOne Labs / Censys | ✅ Exact: **175,108 unique hosts**, 130 countries, 293-day scan, 7.23M observations | SentinelLABS "Silent Brothers", 29 Jan 2026, co-authored with Silas Cutler (Censys) |
| "anonymous AI networks" | ✅ Verbatim from the report's own title ("Ollama Hosts Form Anonymous AI Network Beyond Platform Guardrails") | same |
| Bizarre Bazaar = subscription gateway on stolen Ollama endpoints | ✅ silver.inc, "The Unified LLM API Gateway", 30+ providers at 40-60% discount, crypto/PayPal; targets **Ollama port 11434 without auth** + OpenAI-compatible APIs on 8000; 35,000 sessions, 972 attacks/day | Pillar Security, 28 Jan 2026 |

The claim is a faithful restatement of the quote, and the quote's two attributions both resolve to real, independent, recent primary research. Corroborated by The Hacker News, CybersecurityNews, TechHQ, Cybernews.

**The one real defect:** the word "chaînés/chained." SentinelLABS documents *exposure and capability* (48% tool-calling, 22% vision), **not** confirmed hijacking of those 175k hosts. Splicing the exposure survey against the Bizarre Bazaar campaign invites the unestablished inference that 175k hosts are the gateway's inventory — Bizarre Bazaar's documented scale is 972 attacks/day, not 175k captured hosts. That's a quali