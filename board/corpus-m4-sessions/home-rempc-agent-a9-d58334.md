[user] Recherche l installation OFFICIELLE de BrowserOS (navigateur agentic open-source ; repo probable github.com/browseros-ai/BrowserOS ; site browseros.com) sur Linux. VERIFIE — ne devine pas :
- curl -s https://api.github.com/repos/browseros-ai/BrowserOS/releases/latest (si le repo/owner differe, trouve le vrai via WebSearch et corrige) pour la DERNIERE version et la liste REELLE des assets Linux (noms de fichiers .deb / .AppImage / .tar.*).
- curl -sI sur l URL de download de l asset Linux pour confirmer HTTP 200 (ou 302 vers un CDN valide).
Determine : (a) est-ce un FORK Chromium — donc pilotable en CDP via --remote-debugging-port ? (b) les artefacts Linux disponibles + leurs URLs EXACTES verifiees, (c) les commandes d install exactes (dpkg -i / chmod +x AppImage / etc.), (d) comment le LANCER avec le port de remote debugging CDP et un --user-data-dir persistant.
Retourne le schema. 'verified' = version tag reelle + chaque URL avec son http status. 'risks' = reversibilite de l install, taille, maintenance.

[assistant] I'll verify the BrowserOS installation info. Let me start by checking the GitHub releases API and loading web tools in parallel.

[assistant] The `latest` endpoint returned a sub-component (BrowserClaw Server Rust v0.0.19), not the main browser. I need the actual browser app release with Linux binaries. Let me list all releases and find Linux assets.

[assistant] Found it. The main desktop browser is tag **v0.47.18** with a `.deb` and `.AppImage`. Let me get full asset details (sizes, exact URLs) and verify the download URLs return HTTP 200/302.

[assistant] Both Linux download URLs return **HTTP 302** redirecting to GitHub's `release-assets.githubusercontent.com` CDN with correct filenames — confirmed valid. Now let me confirm it's a Chromium fork (CDP support) and the installed binary name.

[assistant] WebFetch is being intercepted by context-mode. Let me use ctx_execute to fetch the repo README directly and confirm the Chromium-fork claim plus the installed binary name.

[assistant] Confirmed it's an open-source **Chromium fork** (README lines 39, 112, 249). Now let me pin down the Linux install instructions and the exact installed binary name/path from the docs.

[assistant] Package name is **`browseros`**, version **148.0.7966.97** (Chromium 148 base). Let me read the postinst script to get the exact binary path and any symlink it creates.

[assistant] Binary path confirmed: installs to **`/usr/lib/browseros/`** with executable symlink **`/usr/bin/browseros`** (registered as `x-www-browser`). Let me verify the "stable latest" site download URLs (files.browseros.com / cdn.browseros.com) that the README advertises, then I have everything.

[assistant] Both stable site pointers are live: `cdn.browseros.com/download/BrowserOS.deb` → HTTP 200 (225,669,548 B) and `files.browseros.com/download/BrowserOS.AppImage` → HTTP 200 (297,632,960 B). Let me do one quick local check — whether BrowserOS is already installed/running here (the JARVIS stack references a browseros container), which is directly relevant.

[assistant] I have all verified facts. Key finding: the GitHub `releases/latest` endpoint is misleading (it points to a sub-component of the monorepo, not the browser), and the local `jarvis-browseros` on port 3700 is a separate product, not this Chromium fork. Compiling the structured answer.