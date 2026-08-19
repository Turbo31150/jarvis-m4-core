[user] CONTEXTE STACK (verifie, self-contained): BrowserOS = fork ungoogled-chromium 148 (browseros-ai v0.47.18), AppImage /home/rempc/browsers/BrowserOS.AppImage, headful, DISPLAY=:1, profil PERSISTANT /home/rempc/.browseros-cdp, lance SANS --remote-debugging-port (casse le MCP natif) avec --no-sandbox + --load-extension bitwarden,requestly. Serveur MCP natif: config /home/rempc/.browseros-cdp/.browseros/config.json donne ports {proxy:9000, server:9200, cdp:9101}. Endpoint MCP = http://127.0.0.1:9000/mcp (Streamable HTTP JSON-RPC, ~17-23 outils consolides: tabs,navigate,snapshot,act,evaluate,run,screenshot,pdf,execute_action,connector_mcp_servers...). Claude Code deja branche (claude mcp add --transport http browseros http://127.0.0.1:9000/mcp --scope user). Vrai Google Chrome installe /usr/bin/google-chrome = navigateur par defaut, deja loggue Google rem.mesfinances@gmail.com. Ollama UP 127.0.0.1:11434 (modeles: gemma3:27b, gemma3:4b, qwen3:1.7b, mxbai-embed-large). n8n UP conteneur jarvis-n8n 127.0.0.1:5678. Requestly extension Intercept&Modify (MV3) chargee dans le profil. Doc BrowserOS=docs.browseros.com (+ /llms.txt). Doc Requestly=docs.requestly.com/llms-full.txt. INTERDIT: chrome-devtools-mcp (verdict NO-GO board #607).

DOMAINE 2 — ANTI-DETECTION via Requestly. Objectif Remi: naviguer en automatise sans se faire virer par les sites qui detectent l'IA/automation. TACHE: produis un SET DE REGLES REQUESTLY concret + importable (ou pas-a-pas exact) pour: (1) normaliser User-Age

[assistant] I'll research the Requestly rule format and probe the actual browser versions to build coherent anti-detection rules. Let me start in parallel.

[assistant] BrowserOS runs Chromium 148.0.7966.97 (default Chrome is 150) — coherence matters, so I'll build headers around Chrome 148 to match the real JS engine. Now let me pull the exact Requestly rule JSON schema.

[assistant] WebFetch is routed through context-mode here. Let me load those tools and fetch/index the Requestly docs.

[assistant] Let me fetch and index the Requestly docs, plus verify the current Chrome 148 UA/client-hint format via a quick search.

[assistant] Now let me query the indexed docs for the exact JSON schema of the three rule types.

[assistant] The docs confirm UI behavior (JS load-time: "As Soon As Possible" = before page load, "After Page Load"; CSS applies immediately). The llms-full is UI-oriented and doesn't contain the raw export schema. Let me verify the exact export JSON schema against Requestly's open-source rule definitions and confirm the Chrome 148 client-hint format.

[assistant] I have everything I need. Key verified facts are locked in. Let me compile the deliverable.

Verified findings before I write the output:
- BrowserOS = Chromium **148.0.7966.97** (from config.json); default Chrome is 150.0.7871.186. Coherence → present as Chrome **148** (the real engine), which means the browser's **native Sec-CH-UA is already correct** and should NOT be fabricated.
- Requestly docs confirm: Insert Scripts injects JS into the page DOM; JS load-time options are "As Soon As Possible" (= `beforePageLoad`, document_start) and "After Page Load" (= `afterPageLoad`); CSS applies immediately.
- MDN/http.dev confirm the Sec-CH-UA **GREASE brand is deliberately randomized per Chrome release** — no canonical fixed string; anti-bot vendors keep per-version GREASE maps, so a wrong hardcoded value is itself a detection signal.