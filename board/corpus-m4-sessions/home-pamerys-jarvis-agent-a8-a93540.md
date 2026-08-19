[user] CONTEXTE: machine M4 (pamerys-m4), uid=1000(pamerys), repo /home/pamerys/jarvis.
REGLE ABSOLUE: LECTURE SEULE. Tu ne modifies AUCUN fichier, tu ne demarres/arretes AUCUN service,
tu ne fais AUCUN git commit. Uniquement: cat, ls, grep, find, head, sed -n, sqlite3 en SELECT, --help.
REGLE DOCKER: la commande 'docker' locale est BLOQUEE par un hook (pile perimee).
Utilise TOUJOURS /home/pamerys/jarvis/bin/jarvis-docker a la place.
REGLE ZERO-HALLUCINATION: chaque affirmation doit citer un chemin de fichier reel + un extrait reel.
Si tu n'as pas verifie, dis "NON VERIFIE". N'invente jamais un nom de script ou une option CLI.
Reponds en francais.

MISSION — VERIFICATION ADVERSARIALE.
Un agent explorateur pretend ceci (axe boot-containers):
  chemin: /home/pamerys/jarvis/scripts/swarm-persistance.sh
  role pretendu: Rend persistantes les donnees d'un service Swarm en stockage volatil : localise le noeud, verifie le volume de donnees, extrait, seme un volume, puis monte. 115 lignes.
  commande pretendue: /home/pamerys/jarvis/scripts/swarm-persistance.sh <service> <chemin-donnees> [uid:gid]
ex: swarm-persistance.sh jarvis-full-stack_n8n /home/node/.n8n 1000:1000
  preuve fournie: Revele un risque structurel reel, entete l.9-11 : 'CONTEXTE (investigation 2026-08-01) : aucun service de la pile jarvis-full-stack ne declare de volume. Leurs donnees vivent dans la couche inscriptible du conteneur — toute recreation (update, reboot, replanification) les efface.' Garde-fous serieux : MIN_BY

[assistant] File exists, 115 lines, SSH aliases confirmed. Now let me read the actual script content.

[assistant] Now let me hunt for the hard-coded fallback trap and cross-check the claimed line numbers precisely.

[assistant] All docker calls are remote-via-SSH (local hook irrelevant), and every `|| echo 0` fallback routes to a `die` or an honest warning — no false-success. Let me prove the CLI contract safely and check the wired skill.