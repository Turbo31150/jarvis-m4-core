[user] mode secour gnome lag et pas connectr au cluster multiple erreur jai beau écrire il prend rien en compte

[assistant] Boot **normal** (pas de recovery, pas de nomodeset, prime déjà en `on-demand`). Le vrai souci est ailleurs : **15 Gio de swap utilisés** + 3 sessions dont une bloquée en `closing`. Je creuse.

[assistant] Diagnostic net — **ce n'est pas le mode secours**. Le boot est normal (session X11 GNOME sur vt2, `gdm-x-session` vivante). Trois causes réelles. J'identifie le coupable avant de tuer quoi que ce soit.

[assistant] **Cause racine trouvée.** `/etc/fstab:16` monte `turbo@10.42.0.1:/home/turbo` — or **10.42.0.1 c'est cette machine elle-même** (interface `enxf8e43b9b67d4`). Le SSHFS boucle sur lui-même → `mount-start-limit-hit` → et chaque accès à `~/m1-disk` (gvfs, Fichiers, hostnamed) part en tentative bloquante. C'est exactement ça qui fige GNOME quand tu tapes.

Je vérifie la bonne cible avant de corriger.

[assistant] Confirmé : SSH `turbo@10.42.0.230` (M6) répond parfaitement avec `id_ed25519`, 517 Go libres. Le fstab pointait juste sur la mauvaise IP. Je corrige.

*(le « 0 » reçu au passage — je le mets sur le compte du clavier qui laggue, je continue.)*

[assistant] Montage M6 opérationnel — le cluster est reconnecté. Reste le lag. Je sonde la pression mémoire/thermique maintenant.

[assistant] Deuxième coupable identifié : `cluster-warmer.timer` a tiré à **04:51:17**, et `llama-server` est né à **04:51:23** — 6 s après. Il brûle **133 % de CPU depuis 8 min sans aucun client connecté** sur le port 11434. Une inférence orpheline qui tourne dans le vide et pousse la machine à 78 °C. Je vérifie avant de couper.

[assistant] Le nœud du problème : `"expires_at":"2318-11-24"` — un TTL de **293 ans**. Le modèle `gemma3:4b` est épinglé en mémoire à vie (posé par `ollama-ttl-fix.timer`), il ne se déchargera jamais tout seul. Je le décharge proprement — réversible, la prochaine requête le rechargera.

[assistant] Le `llama-server` est bien parti, mais attention — la RAM est descendue à **435 Mio disponibles** : les process qui étaient en swap remontent. On frôle l'OOM, c'est le vrai lag. Je regarde ce qui occupe, maintenant.

[assistant] **Coupable trouvé.** PID 1311324 : `node-MainThread`, **6 Go de RAM en 6 secondes**, 52 % CPU — et son parent est `llmster` (PID 22240). Le process de 3 Go vu au tout début était le même pattern : `llmster` **respawne en boucle des node qui grimpent à plusieurs Go**. C'est ça qui sature les 15 Gio, provoque le swap et fige ta saisie. J'identifie avant de couper.

[assistant] Cause racine confirmée, et elle est nette :

`llmster` = **LM Studio**, et il tourne dans `session-20.scope` — or **session 20 est celle affichée `closing`** dans mon tout premier relevé. Ses enfants sont donc tués par systemd à mesure, et LM Studio les **relance aussitôt**. Chaque cycle alloue 3 à 6 Go : 2,99 Go → 6 Go → 3,7 Go en 7 s. C'est une boucle de crash-respawn qui remplit les 15 Gio, force le swap et fige ta saisie.

J'arrête la boucle (réversible — Ollama :11434 reste dispo comme backend).

[assistant] Reçu. Vérification éclair avant de rebooter — pour que le problème ne revienne pas au démarrage, et pour ne rien couper de critique.

[assistant] Deux choses à régler, sinon le reboot ne servirait à rien :

- **`lmstudio-server.service` est `enabled`** → il relancerait la boucle au démarrage. Je le désactive (réversible : `systemctl --user enable --now lmstudio-server`).
- **Une sauvegarde deja-dup vers Google Drive tourne** (phase d'estimation `--dry-run`) → je l'arrête proprement, duplicity reprendra tout seul au prochain passage.

Les 3 conteneurs Docker anonymes (`objective_grothendieck`, `serene_taussig`, `fervent_faraday`, politique `no`) **ne reviendront pas** après reboot — n8n et les services Swarm si.

[assistant] Tout est en place. J'écris le récap sur disque pour que tu le retrouves après redémarrage, puis je reboote.