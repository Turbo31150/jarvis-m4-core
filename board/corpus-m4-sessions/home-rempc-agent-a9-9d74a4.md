[user] CONTEXTE STACK (verifie, self-contained): BrowserOS = fork ungoogled-chromium 148 (browseros-ai v0.47.18), AppImage /home/rempc/browsers/BrowserOS.AppImage, headful, DISPLAY=:1, profil PERSISTANT /home/rempc/.browseros-cdp, lance SANS --remote-debugging-port (casse le MCP natif) avec --no-sandbox + --load-extension bitwarden,requestly. Serveur MCP natif: config /home/rempc/.browseros-cdp/.browseros/config.json donne ports {proxy:9000, server:9200, cdp:9101}. Endpoint MCP = http://127.0.0.1:9000/mcp (Streamable HTTP JSON-RPC, ~17-23 outils consolides: tabs,navigate,snapshot,act,evaluate,run,screenshot,pdf,execute_action,connector_mcp_servers...). Claude Code deja branche (claude mcp add --transport http browseros http://127.0.0.1:9000/mcp --scope user). Vrai Google Chrome installe /usr/bin/google-chrome = navigateur par defaut, deja loggue Google rem.mesfinances@gmail.com. Ollama UP 127.0.0.1:11434 (modeles: gemma3:27b, gemma3:4b, qwen3:1.7b, mxbai-embed-large). n8n UP conteneur jarvis-n8n 127.0.0.1:5678. Requestly extension Intercept&Modify (MV3) chargee dans le profil. Doc BrowserOS=docs.browseros.com (+ /llms.txt). Doc Requestly=docs.requestly.com/llms-full.txt. INTERDIT: chrome-devtools-mcp (verdict NO-GO board #607).

DOMAINE 4 — ORCHESTRATION Ollama -> n8n -> BrowserOS (tache #5). TACHE, plan concret + commandes exactes: (a) mettre Ollama (gemma3:27b) comme PROVIDER LLM de l'agent BrowserOS: via config file (/home/rempc/.browseros-cdp/.browseros/config.json ou chrome://b

[assistant] I'll investigate the actual environment first, then fetch the authoritative docs, before producing the concrete plan.

[assistant] Strong signal already. Key catches: gemma3:27b advertises only `["completion"]` (no `tools` capability), Ollama has NO `OLLAMA_CONTEXT_LENGTH` set, and jarvis-n8n is on a custom bridge `jarvis-network` with empty ExtraHosts (no host.docker.internal). Let me dig into the network path, the BrowserOS profile prefs, and fetch the docs.

[assistant] The container gets "connection refused" on the gateway IP, which strongly implies BrowserOS binds 9000 to 127.0.0.1 only. Let me confirm the listen address and extract the exact provider block from BrowserOS Preferences, then fetch the three docs.

[assistant] BrowserOS ports 9000/9200/9101 did NOT appear in `ss` — only ollama's `*:11434`. I need to confirm whether BrowserOS is even listening and on which interface, then fetch the docs.

[assistant] Docs are client-rendered; the `.md` variants exist. Also critical: ports 9000/9200/9101 are NOT listening right now (`curl` to 9000 = http 000, `ss`/`lsof` empty) — the native MCP server is down, only the stdio bridge (PID 155280) and the jarvis-browseros container are up. Let me pull the markdown docs and check the server log.

[assistant] The server log is decisive: BrowserOS binds "HTTP server listening on http://127.0.0.1:9200" (loopback), and it was SIGTERM'd (currently down — explains the empty `ss`). Config flag `allow_remote_in_mcp:false` is likely the remote-bind gate. Let me read the full markdown docs now.

[assistant] Docs fully retrieved. The critical reconciliation: BrowserOS's OWN docs say Agent Mode = "Cloud models only... Local LLMs aren't powerful for most agentic tasks yet" (local is for Chat Mode), and gemma3:27b in Ollama exposes no `tools` capability. Let me verify a few last things: socat availability on host, GPU/VRAM headroom, n8n volume persistence, and re-confirm the current MCP listen state.

[assistant] Major hardware finding: the GPU is a GTX 1050 with only 4 GB VRAM. gemma3:27b is 17 GB — it will run almost entirely on CPU, which is very slow and collides with BrowserOS's 10-minute agent timeout. Let me get the n8n mount/compose result.

[assistant] n8n's `.n8n` is a named volume (`jarvis_n8n_data`) so community nodes persist. Let me grab the exact n8n service block from the compose to give precise edits.

[assistant] I have everything verified. The compose already uses the convention `host.docker.internal:172.18.0.1` for another service, n8n has none, `.n8n` is a persistent named volume, socat is on the host, and the GPU is a 4 GB GTX 1050. Compiling the final plan.