[user] STACK: BrowserOS = service systemd 'browseros.service' actif, MCP natif http://127.0.0.1:9000/mcp (Streamable HTTP stateless, 23 outils: tabs,navigate,snapshot,act,screenshot,evaluate,run...). Aussi expose Tailscale https://jarvis-dva.tail1065ac.ts.net:9443/mcp. n8n = conteneur docker 'jarvis-n8n' sur 127.0.0.1:5678. Ollama 127.0.0.1:11434 (gemma3:27b). Requestly extension MV3 chargee dans profil /home/rempc/.browseros-cdp. NE PAS redemarrer BrowserOS (service supervise). Le hook context-mode intercepte 'curl <url>' — utiliser python urllib/http.client pour les appels HTTP, pas curl.

DOMAINE multi-client MCP : brancher l endpoint BrowserOS sur les AUTRES clients IA presents (PAS Claude Code, deja fait). ETAPES: (1) detecter les clients installes: which codex cursor gemini opencode zed ; ls ~/.config/{Cursor,Codex,zed,opencode} ~/.codex ~/.cursor 2>/dev/null. (2) pour CHAQUE client present, ajouter le serveur MCP browseros (transport http, url http://127.0.0.1:9000/mcp) dans SON fichier de config, de facon IDEMPOTENTE avec BACKUP horodate, SANS ecraser les serveurs existants. (3) pour Claude Desktop ~/.config/Claude/claude_desktop_config.json : il a deja 'jarvis' + 'filesystem' — AJOUTE une entree 'browseros' via wrapper {command:'npx', args:['mcp-remote','http://127.0.0.1:9000/mcp']} SANS retirer les autres, backup d abord (ATTENTION: si Claude Desktop tourne il peut reecrire au quit — juste preparer + noter). Retourne le schema (files=configs modifies+backups). NE touche PA

[assistant] Let me inspect the config directories and existing files for each detected client.

[assistant] Detection complete. Present clients:
- **Gemini CLI** (binary installed at `/home/rempc/.npm-global/bin/gemini`, config `~/.gemini/settings.json`)
- **Codex** (config `~/.codex/config.toml`, OMC-managed registry with `openspace`)
- **Cursor** (config dir `~/.cursor`, no mcp.json yet, no binary in PATH)
- **Claude Desktop** (`~/.config/Claude/claude_desktop_config.json`, has `jarvis` + `filesystem`)

No `zed`/`opencode`. Let me verify the exact Codex `config.toml` HTTP MCP format via context7 before writing (probe-first), and confirm BrowserOS endpoint is reachable.

[assistant] BrowserOS endpoint is alive. Now let me verify the exact Codex `config.toml` streamable-HTTP MCP format.

[assistant] Codex format confirmed: `[mcp_servers.<name>]` with `url = "..."` is the native streamable-HTTP transport (no experimental flag needed in current versions). Now let me check `npx`/`node` locations and whether Claude Desktop is running (affects the write-on-quit caveat).

[assistant] `npx`/`node` are at `/usr/bin` (standard PATH, Claude Desktop GUI will resolve `npx`), and `mcp-remote` is already cached. Let me definitively check whether the Electron Claude Desktop app is running (vs claude-code CLI).

[assistant] No Electron Claude Desktop app is running (only claude-code CLI processes and BrowserOS.AppImage), and nothing holds `~/.config/Claude` open — so writing the Claude Desktop config now is safe. All formats are confirmed. Let me write all four configs idempotently with timestamped backups.

[assistant] All four written. Let me verify the results: validate each file parses correctly and existing servers are preserved.

[assistant] All four validated: existing servers preserved everywhere (Codex `openspace`, Claude Desktop `filesystem`+`jarvis`+preferences all intact). Let me prove idempotency by re-running the exact same script — it should report zero changes and create zero new backups.

[assistant] Done. All four AI clients now have the BrowserOS MCP server wired in, idempotently, with existing servers preserved and timestamped backups. Idempotency proven (re-run = zero changes, zero new backups).