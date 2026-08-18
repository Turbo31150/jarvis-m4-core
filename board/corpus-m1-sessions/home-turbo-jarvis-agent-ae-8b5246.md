[user] ## Adversarial Claim Verifier (voter 3/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quels sont les risques réels et les pratiques de durcissement d'un serveur LLM auto-hébergé (LM Studio, Ollama, llama.cpp, vLLM) qui écoute sur 0.0.0.0 sans authentification sur un réseau local ? Documenter : incidents et campagnes de scan constatés, capacités d'un attaquant ayant accès à l'endpoint OpenAI-compatible (exfiltration de prompts, abus de calcul, empoisonnement, pivot), et les parades éprouvées (bind loopback + relais authentifié, reverse proxy, mTLS, segmentation, allowlist). Contexte : LM Studio écoute en 0.0.0.0:1234 sur une machine qui porte aussi la base de données et les agents, sur un LAN domestique avec plusieurs nœuds légitimes qui doivent continuer d'y accéder. Question centrale : quelle parade offre le meilleur rapport sécurité/rupture de service ?

## Claim under review
"Un serveur Ollama mal configuré (sans authentification) a été observé en usage réel comme moteur de raisonnement d'un outil offensif automatisé multi-étapes (framework VAPT) — l'exposition sans auth n'est donc pas un risque théorique mais un vecteur exploité en production."

**Source:** https://www.sysdig.com/blog/llmjacking-evolved-attackers-are-using-stolen-ai-compute-to-build-offensive-agentic-tools (primary)
**Supporting quote:** "threat actor using a misconfigured Ollama model server as the reasoning engine for an automated, multi-stage offensive secur

[assistant] I'll verify this claim against the primary source and look for contradicting evidence.

[assistant] Web search budget is exhausted. Let me try corroborating via alternative fetches.

[assistant] Verified the primary source directly (HTTP 200, 289 KB fetched locally, quote extracted verbatim from the page text rather than relying on a summarizer).

**Verbatim from the Sysdig page:** "On June 12, 2026, the Sysdig Threat Research Team (TRT) observed a threat actor using a misconfigured Ollama model server as the reasoning engine for an automated, multi-stage offensive security tool. The actor was not chatting with the model or reselling access. Instead, they wired access to the AI tool into a software pipeline that scans a target, matches it to known vulnerabilities..."

Also verified in-page: "Ollama... listens on port 11434 with no authentication by default, so a server reachable from the internet is free model capacity for anyone who finds it" and "roughly 175,000 publicly exposed Ollama instances across more than 130 countries, corroborated by Cisco". VAPT appears 21 times with operational detail (4 sessions ≈ 6.5 h, IPs 122.183.48.35 / 122.183.48.195 / 47.15.69.15, Indian residential ISPs). Page date: June 17, 2026 — two months old, current.

Refutation attempts that failed: quote is exact not paraphrased; no contradicting source found (CSA Labs + several outlets corroborate, none dispute); Sysdig TRT is the team that originally coined "LLMjacking", reporting its own telemetry with IoCs — primary, not a press release; the finding is observation-based, not a benchmark.

One legitimate qualification (not a refutation of the claim as worded): the victim server was **i