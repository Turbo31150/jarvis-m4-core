[user] Recherche l installation de Requestly (repo github.com/requestly/requestly ; site requestly.com) sur Linux — intercepteur/modificateur de requetes HTTP open-source (extension navigateur MV3 + app desktop). VERIFIE — ne devine pas :
- API GitHub releases (curl -s https://api.github.com/repos/requestly/requestly/releases/latest) pour la version et les assets desktop Linux reels (AppImage/.deb) ; corrige le repo si besoin via WebSearch.
- curl -sI sur les URLs de download pour confirmer HTTP 200/302.
Determine : (a) app DESKTOP Linux (URL verifiee) — utile comme proxy MITM systeme, (b) EXTENSION navigateur : comment l installer dans un Chromium/BrowserOS (Chrome Web Store id, ou build local depuis le repo, ou charger unpacked), (c) comment Requestly s integre a une navigation CDP : proxy systeme vs extension in-browser — modif headers, redirect, mock, insert scripts. (d) steps install exacts.
Retourne le schema. 'verified' = versions + URLs + http status reels. 'risks' = MITM/cert, reversibilite.

[assistant] I'll verify the Requestly installation details on Linux. Let me start by checking the GitHub API and download URLs.

[assistant] The sandbox redirects curl through context-mode. Let me load the tools I need to fetch URLs directly.

[assistant] The main repo is now just a community hub (changelog-only, no binaries). The real desktop app lives in `http-interceptor-desktop-app` and possibly `requestly-desktop-release`. Let me check those for Linux assets.

[assistant] Desktop app confirmed: latest `v26.6.29` (2026-06-29) in `requestly/http-interceptor-desktop-app`, Linux = AppImage only (no .deb). Now let me verify the download URLs return 200/302 and find the browser extension (Chrome Web Store ID + source repo).

[assistant] The `requestly/interceptor` repo is the real open-source monorepo (TypeScript, actively pushed 2026-07-27, with `browser-extension` + `app` dirs). All download URLs verified (AppImage 302→200). Now let me get the extension build instructions and the Chrome Web Store ID.

[assistant] WebFetch is also proxied. Let me fetch the extension README/build script and scrape the downloads page for store IDs via the sandbox.

[assistant] Let me get the MV3 build/load-unpacked instructions and find the Chrome Web Store ID via search.

[assistant] I have the extension ID `mdnleldcmiljblolnjhpnblkcekpdkpa`. Let me verify the store URL and the downloads/chrome redirect return valid HTTP statuses.