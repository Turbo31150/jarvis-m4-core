[user] CONTRAINTES ABSOLUES (le non-respect invalide ton travail) :
- LECTURE SEULE. Tu ne modifies RIEN : pas de kill, pas de systemctl start/stop/restart,
  pas d'écriture, pas de suppression, pas de git push. Tu OBSERVES et tu RECOMMANDES.
- Le disque /media/pamerys/JARVIS-M1 est physiquement FRAGILE (connexion USB défaillante).
  Lecture seule stricte, jamais d'écriture dessus, et évite les scans exhaustifs longs.
- RGPD : /home/pamerys/jarvis/webapp/ecole.db contient des données d'ÉLÈVES RÉELS.
  Ne lis JAMAIS son contenu. Ne recopie aucun nom d'élève ou de famille nulle part.
- Les fichiers .env / secrets* / *.key / *.pem : tu peux lister leurs CHEMINS,
  jamais leur CONTENU. Ne recopie aucun secret dans ton rapport.
- N'utilise pkill/pgrep -f QUE avec des motifs qui ne matchent pas ta propre ligne
  de commande (piège déjà rencontré : le shell se tue lui-même).
- Machines : M4 = cette machine (/home/pamerys). M6 = ssh turbo@10.42.0.230 (répond mais
  TRÈS chargé, load 11 : mets des timeouts courts, n'insiste pas si ça traîne).
  M1 = OFFLINE, seul son disque USB est lisible. Rémi = 100.113.121.61 (Ollama OK, SSH refusé par ACL Tailscale).
- Si une commande échoue ou timeout, dis-le. Ne prétends jamais avoir vérifié ce que tu n'as pas vu.


MISSION — Localiser les profils Chrome, en vue d'en récupérer un sur M4.

L'utilisatrice a demandé : "récupère le profil Rémi de Chrome sur Chrome M4".
C'est ambigu, il faut lever l'ambiguïté par l'observation.

ATTENTION : un profil Chrome

[assistant] Chrome tourne actuellement sur M4 (SingletonLock actif). Lisons les noms des profils.

[assistant] Un dossier `google-chrome-m1` existe déjà sur M4. Lisons ses profils, plus ceux du disque M1.

[assistant] Le profil « remi » est identifié. Vérifions le disque M1 et comparons les tailles/dates.

[assistant] Chrome n'est pas en cours d'exécution sur M4 (verrou périmé). Lisons les noms de profils sur M6.

[assistant] Comparons les trois copies candidates du profil « remi » et vérifions le point critique du trousseau.

[assistant] Point critique à vérifier : `google-chrome-m1` est-il une copie locale ou un montage distant ?

[assistant] Découverte majeure : conflit de version Chrome. Vérifions le schéma de chiffrement et cherchons « remi » partout.

[assistant] Vérifions la compatibilité des schémas SQLite entre le profil remi (Chrome 151) et Chrome 150 de M4.

[assistant] Dernière vérification : la copie locale sur M4 est-elle complète, et quel emplacement cible est libre ?