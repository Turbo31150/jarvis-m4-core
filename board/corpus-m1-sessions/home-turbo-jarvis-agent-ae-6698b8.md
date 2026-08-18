[user] ## Adversarial Claim Verifier (voter 3/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Quels sont les risques réels et les pratiques de durcissement d'un serveur LLM auto-hébergé (LM Studio, Ollama, llama.cpp, vLLM) qui écoute sur 0.0.0.0 sans authentification sur un réseau local ? Documenter : incidents et campagnes de scan constatés, capacités d'un attaquant ayant accès à l'endpoint OpenAI-compatible (exfiltration de prompts, abus de calcul, empoisonnement, pivot), et les parades éprouvées (bind loopback + relais authentifié, reverse proxy, mTLS, segmentation, allowlist). Contexte : LM Studio écoute en 0.0.0.0:1234 sur une machine qui porte aussi la base de données et les agents, sur un LAN domestique avec plusieurs nœuds légitimes qui doivent continuer d'y accéder. Question centrale : quelle parade offre le meilleur rapport sécurité/rupture de service ?

## Claim under review
"Intezer a conduit un scan Internet actif d'environ 4 500 hôtes sur onze plateformes d'hébergement LLM — les serveurs d'inférence auto-hébergés sont donc une surface scannée systématiquement, pas une menace théorique."

**Source:** https://intezer.com/blog/how-attackers-access-llm-inference/ (primary)
**Supporting quote:** "We scanned roughly 4,500 hosts across eleven of them"

## Checklist
1. Is the claim actually supported by the quote, or is it an overreach/misread?
2. WebSearch for contradicting evidence — does any credible source dispute or heavily qual

[assistant] I'll verify this claim by fetching the primary source and checking for contradicting evidence.

[assistant] Web search budget is exhausted. Let me re-fetch the primary source with a sharper prompt to test the claim's specific wording.

[assistant] Primary source verified verbatim. Web search budget was exhausted (200/200) so I could not hunt independent contradicting sources; I re-fetched the primary twice with different prompts to test wording.

**Findings:**

1. **Quote is verbatim and in context.** Intezer blog (Nicole Fishbein, 3 juin 2026): *"We scanned roughly 4,500 hosts across eleven of them. Every service had open instances, and 14 LocalAI hosts showed active compromise based on attacker-loaded model names consistent with a single automated campaign."* Preceding sentence frames it: *"…that same ease extends to anyone who can access the port."*

2. **The eleven platforms are enumerated** (Ollama, LocalAI, Langflow, n8n, vLLM, ComfyUI, llama.cpp server, Jan, Gradio, + LiteLLM/OpenAI-compatible proxies). Per-platform open rates reported: LocalAI 55 % confirmed open, llama.cpp server 59 % confirmed open — "confirmed open" implies active probing, not passive Shodan lookup only.

3. **The inferential half of the claim holds via a separate datum**, not via the scan itself: a researcher scan proves researchers scan, but the "14 LocalAI hosts showed active compromise … single automated campaign" plus 175 000+ Ollama hosts (prior SentinelOne Labs / Censys work, cited in-article) is what actually supports "pas une menace théorique."

4. **Directly relevant to the user's context**: the article names *at least one exposed LM Studio host* serving `llama3.3-8b-instruct-thinking-heretic-uncensored-claude-4.5-opus-high-reasoni