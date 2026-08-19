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


MISSION — Tranch

[assistant] Chrome est bien arrêté. Trois répertoires de profils existent : `Default`, `Profile 2`, `Profile 4`. Je lis maintenant la source de vérité (`Local State`).

[assistant] Point important : `Local State` connaît **5** profils mais seuls **3** répertoires existent. Je vérifie les `Preferences` locaux puis le disque M1 (lecture seule).

[assistant] Le disque M1 est monté en `rw` — je m'en tiens strictement à la lecture. Inventaire des variantes navigateur sur M1.

[assistant] **Trouvé.** `Profile 4` sur le disque M1 s'appelle `remi`. Je mesure et vérifie le piège de collision.

[assistant] Profil `remi` = 179 Mo. Je vérifie les versions Chrome et le mode de chiffrement (point critique pour les mots de passe).

[assistant] Trois pièges majeurs identifiés. Je mesure précisément avec un `rsync --dry-run` (aucune écriture).

[assistant] Dry-run concluant. Dernier point mesurable : la compatibilité de schéma des bases (M1 tourne Chrome 151, M4 tourne 150).

[assistant] Schémas **identiques** — l'écart de version ne bloque pas. Je prépare maintenant le script de récupération (créé, **non exécuté**).

[assistant] Inventaire terminé, script prêt et validé syntaxiquement, aucune copie effectuée.