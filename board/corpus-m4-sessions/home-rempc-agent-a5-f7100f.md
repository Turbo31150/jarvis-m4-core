[user] MISSION: aspirer TOUTE la doc technique de Requestly (le vrai code open-source). Sois EXHAUSTIF.
SOURCES a lire integralement via l outil MCP repomix (pack_remote_repository):
- github.com/requestly/interceptor (le monorepo source ; cible browser-extension/mv3, README, docs, packages).
- github.com/requestly/http-interceptor-desktop-app (l app desktop AppImage ; README, build, usage proxy).
OBJECTIF METIER: Remi veut charger Requestly DANS un profil BrowserOS/Chromium pilote en CDP pour intercepter/modifier les requetes. Capture: comment installer l extension (unpacked build, Web Store id mdnleldcmiljblolnjhpnblkcekpdkpa), l API des regles (declarativeNetRequest MV3, redirect, modify headers, replace, mock, insert script, delay), comment scripter/importer des regles, format de config/rules JSON, integration proxy desktop vs extension.
Retourne le schema: digest_markdown EXHAUSTIF + urls_read + key_facts.

[assistant] I'll start by loading the repomix MCP tool schemas, then pack both repositories.

[assistant] Both repos packed. The interceptor monorepo is large (mostly SVG assets). Let me build a line-number index for the files that matter, then read them. I'll locate the key files across docs, browser-extension/mv3, and rule processors.

[assistant] I have a complete line-number index. Now let me read the key technical files in batches. First: the MV3 extension architecture, build/install scripts, and config generation.

[assistant] Excellent detail. Now let me read the browser-extension build/install scripts, top-level README, config generation, and static rules JSON.

[assistant] Now the rule types documentation and the interceptor docs (browser-extension vs desktop proxy).

[assistant] Now the second half of rule types (modify request/response body, user agents, redirect, replace) plus the public API create-rule schema.

[assistant] Now the most load-bearing pieces for scripting: the public API rule JSON schema and the actual rule JSON test fixtures. Let me read the public-apis section and the rule JSON fixtures + types.

[assistant] This is the gold — the Requestly rule JSON schema and how it compiles to DNR `extensionRules`. Now let me read the actual rule JSON fixtures (importable format) plus the TS types, and then the interceptor integration docs.

[assistant] Now the interceptor integration docs (browser extension vs desktop app proxy) — key for Rémi's business goal.

[assistant] Now the interceptor overview + browser-extension.mdx + desktop-app.mdx, and the getting-started setup guides.

[assistant] Let me check for the manifest, declarativeNetRequest permissions, and the Web Store ID in the pack, and read the remaining rule fixtures (header/query/request/replace/cancel) plus the top-level README and getting-started.

[assistant] Now the header, query, request, and replace rule fixtures to capture their exact JSON schema.

[assistant] I have all rule JSON schemas now. Let me read the interceptor top-level README (architecture, store links, manual install) and getting-started.md.

[assistant] Let me capture the "difference between desktop app and extension" doc (key for Rémi's decision) and the QueryParam rule fixture, then move to the desktop app repo.

[assistant] Interceptor repo fully covered. Now the desktop app repo. Let me index its key files (README, proxy, chromium launcher, main).

[assistant] Now let me read the desktop app README, package.json, proxy config, and chromium launcher.

[assistant] Now the Chromium launcher (how the desktop proxy launches a browser with `--proxy-server`) and the desktop package.json (build/AppImage config).

[assistant] Let me capture the desktop proxy config constants (PROXY_HOST, ports) and how the proxy fetches rules.