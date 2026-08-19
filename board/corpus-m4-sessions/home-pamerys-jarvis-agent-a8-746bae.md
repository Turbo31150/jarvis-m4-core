[user] CONTEXTE: machine M4 (pamerys-m4), uid=1000(pamerys), repo /home/pamerys/jarvis.
REGLE ABSOLUE: LECTURE SEULE. Tu ne modifies AUCUN fichier, tu ne demarres/arretes AUCUN service,
tu ne fais AUCUN git commit. Uniquement: cat, ls, grep, find, head, sed -n, sqlite3 en SELECT, --help.
REGLE DOCKER: la commande 'docker' locale est BLOQUEE par un hook (pile perimee).
Utilise TOUJOURS /home/pamerys/jarvis/bin/jarvis-docker a la place.
REGLE ZERO-HALLUCINATION: chaque affirmation doit citer un chemin de fichier reel + un extrait reel.
Si tu n'as pas verifie, dis "NON VERIFIE". N'invente jamais un nom de script ou une option CLI.
Reponds en francais.

MISSION — Axe OUTILS MCP & PLUGINS.
1. Parse /home/pamerys/jarvis/.mcp.json (91 serveurs) avec python3: pour chaque serveur -> nom, type
   (stdio/http/sse), commande, si le binaire/chemin de la commande EXISTE reellement sur le disque.
   Compte: combien de serveurs pointent vers un executable/fichier INEXISTANT (= morts).
2. Meme travail sur les serveurs MCP declares dans ~/.claude.json (attention: gros fichier, utilise python3
   pour extraire uniquement les cles mcpServers, ne l'affiche pas en entier).
   Compare les deux listes: quels serveurs sont dans l'un et pas l'autre ?
3. Lis ~/.claude/mcp-needs-auth-cache.json et ~/.claude/mcp-desactives-20260814.json: que disent-ils ?
4. Plugins: pour chaque dossier de ~/.claude/plugins/ (claude-hud, jarvis-cowork, jarvis-lms-audit,
   jarvis-valises, ultraship, local, marketplaces, quaranti

[assistant] Ma première heuristique confondait les paquets npx avec des chemins. Je corrige.

[assistant] Le cache npx réel est `/home/pamerys/.npm-new-cache/_npx`. Je relance l'analyse complète.

[assistant] `mcp-server-sqlite` est bien installé en local (pip). Je vérifie le cache uv puis j'extrais `~/.claude.json`.

[assistant] Point critique détecté : `known_marketplaces.json` pointe vers `/home/rempc/` et non `/home/pamerys/`. Je vérifie.