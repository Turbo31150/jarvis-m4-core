[user] CONTEXTE: machine M4 (pamerys-m4), uid=1000(pamerys), repo /home/pamerys/jarvis.
REGLE ABSOLUE: LECTURE SEULE. Tu ne modifies AUCUN fichier, tu ne demarres/arretes AUCUN service,
tu ne fais AUCUN git commit. Uniquement: cat, ls, grep, find, head, sed -n, sqlite3 en SELECT, --help.
REGLE DOCKER: la commande 'docker' locale est BLOQUEE par un hook (pile perimee).
Utilise TOUJOURS /home/pamerys/jarvis/bin/jarvis-docker a la place.
REGLE ZERO-HALLUCINATION: chaque affirmation doit citer un chemin de fichier reel + un extrait reel.
Si tu n'as pas verifie, dis "NON VERIFIE". N'invente jamais un nom de script ou une option CLI.
Reponds en francais.

MISSION — Axe CLI & COMMANDES.
1. Inventorie ~/.local/bin/ (212 fichiers) et ~/jarvis/bin/ (53). Pour chacun: type (bash/python/lien),
   executable ou non, 1 ligne de role extraite du header du fichier (commentaire de tete ou docstring).
   Utilise un script python3/bash de lecture. Repere les liens symboliques casses.
2. Focus sur le meta-lanceur: lis ~/.local/bin/jarvis ET ~/jarvis/bin/j INTEGRALEMENT.
   Quelles sous-commandes exposent-ils ? (liste exhaustive extraite du code, pas devinee).
3. Inventorie ~/.claude/commands/*.md (47): nom de la slash-command + description + ce qu'elle declenche.
4. Repere les doublons/versions .bak et les scripts qui font la MEME chose sous 2 noms.
5. Cherche s'il existe deja un dispatcher par mots-cles cote CLI: lis le service systemd system
   'jarvis-multiagent.service' (JARVIS Multi-Agent Keyword 

[assistant] Le service pointe vers `/home/pamerys/jarvis/multiagent/jarvis-router.py`. Lançons l'inventaire complet en parallèle.

[assistant] Deux dispatchers par mots-clés existent. Lisons le méta-lanceur `j`, le CLI `jarvis`, et `skillmp-detect.py`.

[assistant] Découverte majeure: le routeur surveille un fichier inexistant. Lisons maintenant le CLI `jarvis` et `skillmp-detect.py`.

[assistant] `skillmp-detect.py` est un 2e routeur par mots-clés (14 familles regex). Extrayons les sous-commandes de `jarvis_master.py`.

[assistant] Troisième routeur: une **table SQLite `keyword_actions`**. Lisons le seed et le contenu réel de la table.

[assistant] Une 4e brique: `/jarvis:cmd` (253 patterns mot-clé→commande). Lisons-la ainsi que l'orchestrateur `/jarvis`.

[assistant] Vérifions si les 15 agents cibles existent réellement, et le hook de préchargement biblio.

[assistant] Inventaire terminé. Toutes les affirmations sont vérifiées par exécution réelle.