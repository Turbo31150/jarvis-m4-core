[user] CONTEXTE: machine M4 (pamerys-m4), uid=1000(pamerys), repo /home/pamerys/jarvis.
REGLE ABSOLUE: LECTURE SEULE. Tu ne modifies AUCUN fichier, tu ne demarres/arretes AUCUN service,
tu ne fais AUCUN git commit. Uniquement: cat, ls, grep, find, head, sed -n, sqlite3 en SELECT, --help.
REGLE DOCKER: la commande 'docker' locale est BLOQUEE par un hook (pile perimee).
Utilise TOUJOURS /home/pamerys/jarvis/bin/jarvis-docker a la place.
REGLE ZERO-HALLUCINATION: chaque affirmation doit citer un chemin de fichier reel + un extrait reel.
Si tu n'as pas verifie, dis "NON VERIFIE". N'invente jamais un nom de script ou une option CLI.
Reponds en francais.

MISSION — Axe BOOT & CONTAINERS.
Reponds a: "quel mecanisme de DEMARRAGE existe deja, et quel est l'etat reel des conteneurs ?"
1. Lis integralement ~/.local/bin/jarvis-boot-sequencer (et ~/jarvis/bin/preflight-check.sh,
   ~/jarvis/bin/jarvis-status, ~/jarvis/bin/jarvis-docker, ~/jarvis/bin/jarvis-cockpit.sh).
   Pour chacun: son role exact, ses etapes, ses options CLI, s'il est idempotent, s'il est branche a systemd.
2. Etat reel des conteneurs via /home/pamerys/jarvis/bin/jarvis-docker ps -a et 'service ls'.
   Identifie precisement lesquels sont Exited/Created ALORS qu'ils devraient tourner
   (jarvis-telegram, jarvis-mcp, jarvis-litellm...). Distingue conteneur standalone vs tache Swarm
   (une tache Swarm 'Exited' remplacee par une tache 'Up' n'est PAS une panne).
3. Cherche les fichiers docker-compose / stack yml du projet (find ~

[assistant] Découverte majeure: `jarvis-boot-sequencer` ne démarre **rien** (uniquement `print()` + `time.sleep()`). Continuons.

[assistant] Les services Swarm sont tous 1/1. Vérifions la suite de la liste et les détails.

[assistant] Constat clé: `jarvis-litellm` est en `created` avec erreur de bind port 4000 déjà utilisé. Cherchons les fichiers compose/stack.

[assistant] Toutes les tâches Swarm sont Running. Lisons les fichiers de stack et l'état systemd.