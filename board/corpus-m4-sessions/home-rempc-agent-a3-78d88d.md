[user] MISSION: aspirer TOUTE la doc du navigateur BrowserOS (browseros-ai). Sois EXHAUSTIF, c est le but.
SOURCES a lire integralement:
- Repo github.com/browseros-ai/BrowserOS : utilise l outil MCP repomix (pack_remote_repository sur 'browseros-ai/BrowserOS' puis grep_repomix_output / read_repomix_output) pour aspirer README + tout le dossier docs/ + tous les .md. Si trop gros, cible les .md et docs/.
- Cherche aussi la doc de l AGENT/automation et du support CDP (fichiers mentionnant cdp, remote-debugging, agent, MCP, extension).
OBJECTIF METIER: Remi veut piloter BrowserOS en CDP (profil persistant, headful, garder sessions) et cabler ses outils via MCP. Capture donc en priorite: flags de lancement, --remote-debugging-port, --user-data-dir, comment l agent interne fonctionne, API/endpoints exposes, comment charger une extension, config.
Retourne le schema avec un digest_markdown EXHAUSTIF (n hesite pas a etre long) + key_facts atomiques.

[assistant] I'll start by loading the repomix tool schemas and packing the BrowserOS repository.

[assistant] I'll pack the BrowserOS repository, focusing on markdown docs and documentation files first.

[assistant] Repository packed successfully (94 files). The two SVG logos are huge but irrelevant. Let me grep for the mission-critical content (CDP, flags, ports, extension) and read the key docs in parallel.

[assistant] The generic patterns matched the huge SVGs. I have direct filesystem access to the packed XML. Let me locate the key files' line positions and read the mission-critical docs directly.

[assistant] Excellent content on CDP, MCP endpoints, and the agent. Let me read the features docs and package READMEs in parallel.

[assistant] Now the agent packages, which are core to the CDP/MCP/agent mission. Reading them in parallel.

[assistant] Now the CDP protocol README, agent monorepo README, root README, and remaining docs.

[assistant] The last read had a transient error. Let me read the remaining docs (n8n, troubleshooting, index, onboarding) and the browser build CLI which covers how the Chromium fork launches.

[assistant] One read keeps hitting a tool glitch when run in parallel. Let me read the n8n integration and troubleshooting docs sequentially.

[assistant] The offset 4188 window contains a giant single-line SVG that blows the budget. Let me locate the giant SVG lines and confirm what's in that range.

[assistant] Found it: giant logo SVGs at lines 4261-4300. I'll read n8n and troubleshooting while avoiding those lines.

[assistant] Now let me check for any explicit launch flags (remote-debugging-port, user-data-dir, headful) across the whole packed output, and read the browser build CLI.

[assistant] Key finds: launch commands with `--user-data-dir` + remote debugging in contributing.mdx, and a CDP-port section in the ai-sdk skill. Let me read those exact sections.

[assistant] I now have comprehensive coverage of the entire BrowserOS documentation. Let me compile the exhaustive digest.