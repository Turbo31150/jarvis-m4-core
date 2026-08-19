[user] reconnexion installa-tion de chrome récupere tyout de m1 disque dure breancher a monter bowors ow gitmoire et tte

[assistant] Je commence par un état des lieux : disques branchés (à monter), présence de Chrome, services en échec, puis j'agirai (installation Chrome + montage disque + récupération).

[assistant] Confirmé : le wrapper `google-chrome` est orphelin (aucun binaire dans `/opt/google/chrome`). J'installe le paquet officiel.

[assistant] Je vérifie l'état Tailscale local et la connectivité vers `jarvis-franck-m1` (100.112.114.32).

[assistant] Tout est terminé. Bilan complet de la reconnexion et de la récupération :

## ✅ Réseau Tailscale — déjà connecté, rien à réauthentifier
Cette machine **est** `jarvis-franck-m1` (100.112.114.32) : le `tailscale status` est actif, le ping vers cette IP répond en 0,05 ms (local). Pas besoin de `tailscale login` ni de `--reauthenticate`. Le mesh voit 3 autres nœuds (`jarvis-rem-pc-asus`, `jarvis-rem-server-tour-pc`, `rem-s25-android`) et le Funnel est ouvert sur `https://jarvis-m1.tail1065ac.ts.net:8443`.

## ✅ Chrome installé et réparé
- **Google Chrome 151.0.7922.137** installé depuis le deb officiel (le wrapper `~/.local/bin/google-chrome` était orphelin — remplacé par un lien vers le vrai binaire).
- Les **4 lanceurs du Bureau** (Chrome-Franck→Default, Chrome-Claire→Profile 3, Chrome-MiningExpert→Profile 2, Chrome-remi→Profile 4) pointent sur ce chemin et fonctionnent maintenant, rendus exécutables et approuvés GNOME.

## ✅ Disque M1 : récupération fusionnée (~31 Go ajoutés)
Le disque branché (`JARVIS-M1`, sdb2) était déjà monté sur `/mnt/m1`. Découverte importante : **le système local est plus récent que ce disque** (c'est une ancienne image de M1). J'ai donc fusionné en mode *ne-jamais-écraser* (`rsync --ignore-existing`) :
- **Navigateurs** : profils google-chrome (8,5 Go), chromium, Brave — fusionnés.
- **Mémoire** : `.claude` et `.openclaw` (y compris `cron/jobs.json` récupéré via sudo) — fusionnés.
- **Git/SSH** : clés et config fusionnées, permissions 700/600 réappliqu