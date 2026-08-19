[user] CONTRAINTES ABSOLUES :
- Tu EXÉCUTES, mais uniquement des actions RÉVERSIBLES et BORNÉES. Jamais de rm -rf,
  jamais de suppression de données, jamais de git push, jamais de désinstallation.
- MESURE AVANT / MESURE APRÈS. Une action sans preuve chiffrée ne compte pas.
- Le disque /media/pamerys/JARVIS-M1 est FRAGILE (USB défaillant) : LECTURE SEULE stricte,
  jamais d'écriture dessus. Écris tes livrables dans /home/pamerys/sauvegardes/.
- RGPD : /home/pamerys/jarvis/webapp/ecole.db contient des données d'ÉLÈVES RÉELS.
  Ne la lis jamais, ne la copie jamais, ne l'inclus dans aucune archive.
  Ne recopie aucun nom d'élève ou de famille dans ton rapport.
- Secrets (.env, secrets*, *.key, *.pem, keys.txt) : tu peux lister des CHEMINS,
  jamais afficher un CONTENU. Aucun secret dans ton rapport.
- pkill/pgrep -f : n'utilise JAMAIS un motif qui matche ta propre ligne de commande
  (piège déjà rencontré : le shell se tue lui-même). Préfère pkill -x ou le PID.
- Machines : M4 = ici. M6 = ssh turbo@10.42.0.230 (VIENT d'être libéré de 11 boucles,
  il était à load 39 ; mets des timeouts courts et vérifie qu'il respire avant de charger).
  Rémi = 100.113.121.61 (Ollama OK sur :11434, SSH REFUSÉ par ACL Tailscale — n'insiste pas).
  M1 = OFFLINE, seul son disque USB est lisible.
- Si une commande échoue ou timeout, DIS-LE. Ne prétends jamais avoir fait ce que tu n'as pas fait.
- Si une action te paraît dangereuse une fois sur place, NE LA FAIS PAS et explique pourquoi.


MISSION — Fabriq

[assistant] Inventaire lu (partiel, 3108 lignes). Maintenant je mesure le terrain avant de fabriquer quoi que ce soit.

[assistant] 245 Go libres, `age` présent, clé présente. Le disque M1 est monté **rw** — je ne dois donc surtout rien y écrire. Je construis maintenant la liste d'inclusion (approche whitelist + pruning) plutôt qu'un tar aveugle sur 649 Go.

[assistant] Le scan est rapide (cache FS chaud). Je construis la liste d'inclusion avec pruning des dossiers géants.

[assistant] Erreurs = permissions root (pas d'I/O), mais elles touchent des dossiers précieux (`bibliotheque`, `labo`, `sql-backups`). J'analyse plus finement et je teste sudo.

[assistant] `bibliotheque`/`labo`/`sql-backups` ont nlink=2 → probablement vides. Je vérifie avec sudo (disponible) et j'inspecte le gros bruit `jarvis/data`.

[assistant] Les 4 dossiers root sont **vides** (points de montage démontés) — rien à récupérer, sudo inutile. Je filtre maintenant la liste candidate (aucune I/O disque supplémentaire).

[assistant] Trois poids lourds sont des **données runtime**, pas du précieux. Je les retire, puis je copie en local (une seule lecture de l'USB fragile) avant scan et archivage.

[assistant] rsync terminé sans erreur I/O (2 fichiers refusés pour permission root). Maintenant le scan de secrets — le vrai garde-fou.

[assistant] 261 + 315 fichiers suspects. Je regarde **où** ils sont (chemins seulement, jamais le contenu) avant de les retirer.

[assistant] Confirmation nette : de **vrais secrets** sont présents (55 clés `sk-ant-`, 123 clés Google `AIza`, 13 tokens GitHub, 9 AWS, 48 JWT). Le filtrage par nom seul n'aurait rien attrapé. Je les retire du staging (la source M1 reste intacte — aucune duplication de secret sur M4).

[assistant] 143 Mo à partir de 649 Go. Maintenant la vérification **sur l'archive elle-même**, pas sur le staging.

[assistant] Les 341 sont des faux positifs de mon regex : le mot "token" apparaît dans le **nom de projet** `jarvis-zero-token`. Je vérifie sur le basename seul, puis le contenu réel de l'archive.

[assistant] 12 + 8 occurrences résiduelles — mon scan initial utilisait `-I` (saute les fichiers binaires). Je re-scanne **sans** cette option.

[assistant] Le staging est propre à 0 (binaires inclus). Les 12+8 sont donc des artefacts de concaténation du flux `tar -O`. Preuve définitive : j'extrais l'archive et je scanne fichier par fichier.

[assistant] Preuve définitive : **0 secret**, 66 029 fichiers, profil = doc/python/json/shell. Maintenant la clé age et le chiffrement.

[assistant] Dernière vérification : santé du disque M1 et preuve qu'aucune écriture n'y a été faite.

[assistant] Gitmore fabriqué, vérifié et chiffré. Aucune erreur I/O sur `sda2`, et zéro écriture sur le disque M1.