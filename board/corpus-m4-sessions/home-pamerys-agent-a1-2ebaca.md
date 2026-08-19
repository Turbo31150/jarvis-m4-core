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


MISSION — Vérifi

[assistant] I'll verify each correctif with real commands. Starting with the Déjà Dup settings and machine state.

[assistant] Déjà Dup persisté et `$HOME/jarvis/webapp` bien exclu. Maintenant l'historique des sauvegardes et l'autostart.

[assistant] Trouvé un point chaud : un manifeste `.part` daté d'hier soir. Je vérifie s'il tourne encore et ce que les sauvegardes passées contiennent (noms de fichiers uniquement, comptage, sans dump).

[assistant] Confirmation nécessaire : `ecole.db` apparaît dans 3 manifestes. Je précise les chemins exacts et je vérifie si l'exclusion était active lors du dernier run.

[assistant] Découverte majeure : `$HOME/Documents/jarvis-backups/*/ecole.db` n'est **pas** couvert par la nouvelle exclusion. Je vérifie si ces copies existent encore.

[assistant] Je vérifie ce qui alimente `Documents/jarvis-backups` et quels timers déclenchent de l'inférence.

[assistant] Presque fini. Dernières vérifications : origine de `Documents/jarvis-backups`, poids des autostarts restants, et timers système.

[assistant] Load remonté à 3,72 — en partie mon propre `find`. Je vérifie un dernier trou puis je remesure au calme.

[assistant] Cause exacte identifiée. Dernier point : qui déclenche ce script, et mesure finale au calme.

[assistant] Trouvé des déclencheurs **hors systemd** (crontab). Je les caractérise rapidement.

[assistant] Vérification terminée. J'ai trouvé un contournement qui rend le correctif RGPD incomplet.