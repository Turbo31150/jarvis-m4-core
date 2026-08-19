[user] STACK: BrowserOS = service systemd 'browseros.service' actif, MCP natif http://127.0.0.1:9000/mcp (Streamable HTTP stateless, 23 outils: tabs,navigate,snapshot,act,screenshot,evaluate,run...). Aussi expose Tailscale https://jarvis-dva.tail1065ac.ts.net:9443/mcp. n8n = conteneur docker 'jarvis-n8n' sur 127.0.0.1:5678. Ollama 127.0.0.1:11434 (gemma3:27b). Requestly extension MV3 chargee dans profil /home/rempc/.browseros-cdp. NE PAS redemarrer BrowserOS (service supervise). Le hook context-mode intercepte 'curl <url>' — utiliser python urllib/http.client pour les appels HTTP, pas curl.

DOMAINE anti-detection : produire des ARTEFACTS prets a importer (n applique RIEN qui redemarre BrowserOS). ETAPES: (1) ecrire /home/rempc/browsers/requestly-antidetect-rules.json = export de regles Requestly au VRAI schema (va lire docs.requestly.com/llms-full.txt pour le format exact d un export de rules) contenant: une regle Modify Headers (Accept-Language coherent, coherence Sec-CH-UA) + une regle Insert Script (executee document-start) qui masque navigator.webdriver=false, corrige window.chrome, navigator.plugins, navigator.languages. (2) ecrire /home/rempc/browsers/antidetect-mask.js = le script JS standalone de masquage. (3) documenter comment importer le JSON dans l extension Requestly (popup -> import). HONNETE dans blockers: ceci reduit la detection BASIQUE mais NE PASSE PAS Cloudflare Turnstile/DataDome/reCAPTCHA (empreintes Canvas/WebGL/JA3-TLS non couvertes par Requestly — c est cot

[assistant] I'll start by fetching the Requestly documentation to understand the exact export schema, then create the artifacts.

[assistant] I fetched the docs. Let me search for the exact export schema for Requestly rules.

[assistant] The rules schema isn't in the docs (they're API-client focused). Let me get the authoritative rule schema from Requestly's open-source repo.

[assistant] Found the schema files. Let me fetch the authoritative type definitions for headers rules, script rules, and the base rule schema.

[assistant] Now let me find the exact export/import file format (the wrapper the extension writes/reads).

[assistant] Let me confirm the exact fields the rule processors consume (headers + script), to guarantee the rules actually fire.

[assistant] Let me check for a real rule fixture and the MV3 conversion to nail the exact `version`/field expectations.

[assistant] This confirms the modern Headers schema (`version: 2`, `schemaVersion: "3.0.0"`, `modifications.Request/Response`). Now the Script rule parser to nail script fields and load-time mapping.

[assistant] The Script rule's DNR part only strips CSP; the actual injection is done by the content script. Let me confirm it injects into the page's MAIN world at document_start (critical for `navigator` overrides to affect the page).

[assistant] `world: "MAIN"` + `injectImmediately: true` confirmed — the injected script runs in page context. `loadTime: "beforePageLoad"` runs it immediately. Let me verify the URL matcher so my source pattern actually matches all pages.

[assistant] Confirmed: `Contains` uses `indexOf`, so value `"http"` matches all web pages. Now the critical DNR detail — whether the headers rule includes `main_frame` (DNR excludes it by default). Let me check the headers parser.

[assistant] Header rules need an explicit resourceType filter to cover `main_frame`. Let me get `parseFiltersFromSource` and the ResourceType enum values.

[assistant] Let me confirm the resource-type string values the UI stores in filters (they're cast verbatim to DNR types).

[assistant] I have the complete, verified schema. Key facts confirmed from source:
- Export file = flat JSON array of records (`prepareContentToExport`).
- Headers rule: `version:2`, `schemaVersion:"3.0.0"`, `pairs[].modifications.Request/Response[]`, source `{key,operator,value}`, resourceType filter values are DNR strings (`main_frame`, `xmlhttprequest`, ...).
- Script rule: `pairs[0].scripts[]` with `codeType:"js"`, `type:"code"`, `loadTime:"beforePageLoad"`; injected `world:"MAIN"`, `injectImmediately:true`.
- Import forces status → INACTIVE, so rules must be enabled after import.

Now let me write the standalone mask script.

[assistant] JS is valid. Now let me build the JSON export by embedding the exact mask content, using the verified schema.

[assistant] Now let me validate the JSON is well-formed and the embedded script round-trips exactly to the standalone file.

[assistant] Both artifacts are written and fully validated against the real Requestly source schema. No BrowserOS process was touched (only file writes + `node --check`/`python` validation). Let me record the outcome.