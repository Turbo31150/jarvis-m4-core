[user] ## Adversarial Claim Verifier (voter 2/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quels sont les risques réels et les pratiques de durcissement d'un serveur LLM auto-hébergé (LM Studio, Ollama, llama.cpp, vLLM) qui écoute sur 0.0.0.0 sans authentification sur un réseau local ? Documenter : incidents et campagnes de scan constatés, capacités d'un attaquant ayant accès à l'endpoint OpenAI-compatible (exfiltration de prompts, abus de calcul, empoisonnement, pivot), et les parades éprouvées (bind loopback + relais authentifié, reverse proxy, mTLS, segmentation, allowlist). Contexte : LM Studio écoute en 0.0.0.0:1234 sur une machine qui porte aussi la base de données et les agents, sur un LAN domestique avec plusieurs nœuds légitimes qui doivent continuer d'y accéder. Question centrale : quelle parade offre le meilleur rapport sécurité/rupture de service ?

## Claim under review
"Un serveur Ollama mal configuré (sans authentification) a été observé en usage réel comme moteur de raisonnement d'un outil offensif automatisé multi-étapes (framework VAPT) — l'exposition sans auth n'est donc pas un risque théorique mais un vecteur exploité en production."

**Source:** https://www.sysdig.com/blog/llmjacking-evolved-attackers-are-using-stolen-ai-compute-to-build-offensive-agentic-tools (primary)
**Supporting quote:** "threat actor using a misconfigured Ollama model server as the reasoning engine for an automated, multi-stage offensive secur

[assistant] I'll verify this claim against the primary source and look for contradicting evidence.

[assistant] WebSearch budget is exhausted. Let me attempt independent corroboration via direct fetches.

[assistant] **Verification result: the claim survives.** Key checks:

- **Quote fidelity**: verbatim in the primary source — "the Sysdig Threat Research Team (TRT) observed a threat actor using a misconfigured Ollama model server as the reasoning engine for an automated, multi-stage offensive security tool."
- **Source strength**: Sysdig TRT (the team that coined "LLMjacking"), published 2026-06-17, with IOCs (four sessions from Indian residential IPs 122.183.48.82/.35/.195, 47.15.69.15; markers `VAPTb3gin`/`VAPTfin`) and documented tool stages.
- **Corroboration**: CSA Labs research note, plus VPNCentral/Eye on AI/bruno.digital coverage. No dispute found.
- **Caveats that do not refute**: Sysdig itself hedges on intent ("could be used for legitimate activities"), targets were RFC 1918 / HackTheBox lab ranges (no confirmed downstream victim), and the abused server was **internet-exposed on 11434**, not LAN-only. The claim asserts only that the unauth endpoint was abused as a reasoning engine — which is exactly what was observed.

Sources: [Sysdig](https://www.sysdig.com/blog/llmjacking-evolved-attackers-are-using-stolen-ai-compute-to-build-offensive-agentic-tools), [CSA Labs](https://labs.cloudsecurityalliance.org/research/csa-research-note-llmjacking-evolved-offensive-agentic-tools/)