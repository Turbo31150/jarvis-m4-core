[user] CONTEXTE: machine M4 (pamerys-m4), uid=1000(pamerys), repo /home/pamerys/jarvis.
REGLE ABSOLUE: LECTURE SEULE. Tu ne modifies AUCUN fichier, tu ne demarres/arretes AUCUN service,
tu ne fais AUCUN git commit. Uniquement: cat, ls, grep, find, head, sed -n, sqlite3 en SELECT, --help.
REGLE DOCKER: la commande 'docker' locale est BLOQUEE par un hook (pile perimee).
Utilise TOUJOURS /home/pamerys/jarvis/bin/jarvis-docker a la place.
REGLE ZERO-HALLUCINATION: chaque affirmation doit citer un chemin de fichier reel + un extrait reel.
Si tu n'as pas verifie, dis "NON VERIFIE". N'invente jamais un nom de script ou une option CLI.
Reponds en francais.

MISSION — Axe INDEX MOTS-CLES & PRECHARGEMENT (le coeur de la demande).
La demande de l'utilisateur est: "demarrage containers agents outil tool plugin cli skill commande mots cles precharger"
= il veut qu'au demarrage, TOUT soit precharge et adressable par MOTS-CLES.
1. Recense TOUT index de mots-cles existant sur la machine:
   - tables sqlite contenant 'keyword','mot','trigger','lexique','routing','registry' dans leur nom ou schema.
     Balaye ~/jarvis/databases/*.db et ~/jarvis/*.db avec sqlite3 '.tables' puis '.schema' ciblee.
     ATTENTION: /home/pamerys/jarvis/board/board.db est un LIEN vers ~/jarvis/databases/board.db.
   - fichiers json/yaml/py contenant un mapping mot-cle -> agent/skill/commande
     (grep -rl --include='*.json' --include='*.py' --include='*.yaml' -iE 'mots?_?cles|keywords|triggers|lexique' ~/jarvis ~/.claude

[assistant] Vérification cruciale : quels hooks déclarés existent réellement, et lesquels ne sont pas câblés.

[assistant] Le `routeur.db` est un registre FTS5 unifié. J'analyse sa composition et sa fraîcheur.

[assistant] Point critique : les origines pointent vers `/home/rempc/`. Je vérifie si c'est local ou importé.

[assistant] Trouvé : `jv-registry-build.py`, `build-routing-index.py`, `tool_preloader.py`. J'inspecte ces briques.