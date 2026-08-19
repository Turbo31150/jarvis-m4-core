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


MISSION — Finir 

[assistant] Load 13,07 (<15) mais l'I/O pressure est encore à 73-90%. J'identifie les procs bloqués avant de charger quoi que ce soit.

[assistant] Load à 13 et en baisse (13 / 19,8 / 17,3). J'identifie la vraie cause de l'I/O pressure avant de charger.

[assistant] Disque `sdb` saturé à 73,65 % (write await 230 ms) — c'est lui le goulot. Je vérifie LM Studio (le check précédent a timeout).

[assistant] `lms` est présent (installé aujourd'hui 02:05), :1234 muet, Ollama vivant sur :11434. Un `lms-runaway-guard.sh` tourne — je vérifie qu'il ne va pas tuer mon serveur avant de le démarrer.

[assistant] Le garde ne décharge qu'un modèle bloqué >540 s en génération — sans danger pour le serveur. Je démarre LM Studio headless.

[assistant] L'AppImage existe et il y a déjà une méthode éprouvée harvestée. Je lis la bibliothèque avant de réinventer.

[assistant] LM Studio servait encore sur M6 jusqu'à 02:51 aujourd'hui (4 modèles). Il est tombé. Je cherche le bon lanceur.

[assistant] Il existe un service dédié `lmstudio-server.service` (AppImage LAN :1234), inactif. Je le lis puis le démarre.

[assistant] Le unit contient les UUID des 6 GPU de **M1**, pas ceux de M6. Je récupère les vrais UUID de M6.

[assistant] Cause trouvée : le unit liste 5 UUID de GPU **M1**. Sur M6 seuls 2 existent, et l'UUID invalide en position 2 coupe l'énumération CUDA → **la RTX 3080 est invisible**. Je corrige par un drop-in (réversible) et je liste les modèles.

[assistant] Drop-in appliqué (RTX 3080 en tête). Modèles : Coder-14B 8,37 Go (trop juste), **Qwen3.5-9B 5,24 Go** (sûr), DeepSeek-R1-8B 4,68 Go. Je démarre le service.

[assistant] La cause n'est pas M6 : c'est l'interface USB-Ethernet **de M4** (`enxf8e43b9b67d4`) qui est tombée. Je cherche une route alternative.

[assistant] Carrier = 0 : le lien physique est mort. M6 n'est pas sur Tailscale. Je cherche s'il a une autre adresse.

[assistant] `sudo -n` fonctionne et l'adaptateur ASIX est toujours présent mais PHY en vrac. Je tente une ré-init du lien (réversible, l'interface ne porte aucun trafic).

[assistant] L'adaptateur M4 se ré-énumère parfaitement (UP, MAC intacte) mais reste `NO-CARRIER` : **le côté M6 ne présente plus de lien**. J'arrête les tentatives (2 faites). Vérification finale de l'état de M4.