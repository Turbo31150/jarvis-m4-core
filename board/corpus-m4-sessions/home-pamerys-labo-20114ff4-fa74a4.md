[user] réparation sourie les deux remise par défault des cvlick et utilisation de la sourie

[assistant] Je remets les réglages souris/clics à leur valeur par défaut. D'abord l'état actuel :

[assistant] Cause trouvée : la souris sans fil **YICHIP 2.4G Receiver Mouse (id=11)** est en `floating slave` — détachée du pointeur maître, donc ses mouvements et clics ne sont plus transmis. Je la rattache et remets les mappings de boutons par défaut :

[assistant] La souris est rattachée au pointeur. Maintenant je remets tous les réglages de clic à leur valeur d'usine :

[assistant] Vérification de la cause racine (pour que ça ne recommence pas au prochain branchement) :

[assistant] Réparation faite.

| Élément | Avant | Après |
|---|---|---|
| Souris sans fil YICHIP (id=11) | `floating slave` — **détachée**, aucun mouvement ni clic transmis | `slave pointer (2)` — rattachée au pointeur |
| Mapping boutons (souris, touchpad, ELAN) | non vérifiable/altéré | `1 2 3 4 5 6 7 8 9` (gauche/milieu/droit standard) |
| Réglages GNOME souris | — | tous remis par défaut |
| Réglages GNOME touchpad | `tap-and-drag false` | remis par défaut (`true`) |
| Accessibilité clic (dwell, clic secondaire par maintien) | — | réinitialisés, tous désactivés |

**La cause** : la souris était en `floating`, c'est-à-dire déclarée dans X11 mais non reliée au curseur — d'où l'absence de clics. Le `xinput reattach` l'a réintégrée.

Deux points d'honnêteté :
- Je n'ai pas pu **tester physiquement** un clic à ta place — teste un clic gauche, droit et un double-clic pour confirmer.
- Le `reattach` n'est **pas persistant** : si tu débranches/rebranches le dongle ou redémarres, le device pourrait redevenir flottant. Je n'ai trouvé aucun script coupable sur le disque (le grep n'a remonté que de la documentation), donc l'origine était probablement un test ponctuel. Si le problème revient au prochain démarrage, dis-le-moi et je pose une règle udev/autostart permanente.

[user] '/home/pamerys/Bureau/RACCORCIS_APPLICATIONS' installer via usb c disque dure ssd  m1  tu lutilise et tu réinstallle cable remet les icone barere des tache rend lers fonctionnellle visible sur le burezau bien ranger

[assistant] Je commence par auditer les 33 raccourcis pour savoir lesquels sont réellement fonctionnels.

[assistant] 27 fonctionnels, 5 cassés. Je vérifie les cibles derrière `bash`/`xdg-open` (un binaire valide ne garantit pas que le script existe) :

[assistant] Cause racine trouvée : **tous ces raccourcis viennent du profil M1 (`/home/turbo/…`)** qui n'existe pas sur cette machine (`/home/pamerys`). Je vérifie d'abord si le disque M1 est monté en USB-C, comme tu l'indiques :

[assistant] Parfait — le SSD M1 est bien monté en USB-C sur `/media/pamerys/JARVIS-M1`. Je vais donc réparer chaque chemin `/home/turbo/…` en le résolvant d'abord vers l'équivalent local, sinon vers le disque M1.

`★ Insight ─────────────────────────────────────`
Un fichier `.desktop` n'est « cassé » que par ses chemins : `Exec` (binaire/script), `Icon` et `Path`. Ces raccourcis ont été importés du profil M1 sans réécriture — d'où le `/home/turbo` fantôme. La subtilité : `turbo@10.42.0.230` dans les lignes SSH est un **nom d'utilisateur distant**, à ne surtout pas réécrire, contrairement aux chemins locaux.
`─────────────────────────────────────────────────`

[assistant] Je note ta vision (email) — je la garderai en mémoire après. Je termine d'abord le chantier des raccourcis.

Trois défauts de plus dans `02_CLUSTER` : `disque-data`/`disque-os` pointent vers `/media/rempc/…` (profil d'une autre machine). Je corrige tout et j'installe proprement :

[assistant] 36 publiés. Maintenant les rendre **visibles sur le bureau** et **épinglés à la barre des tâches** :

[assistant] `ding` (icônes bureau) et `dash-to-panel` (barre des tâches) sont actifs. Je rends les icônes cliquables sans avertissement et je vérifie les favoris existants :

[assistant] Mon test était faux (`ls` échoue si un seul chemin manque). Je le refais correctement :

[assistant] Les 14 favoris de la barre des tâches sont tous valides. J'y ajoute les accès cluster nouvellement réparés :

[assistant] Priorité à la souris. J'audite ce qui a changé **et** je cherche ce qui la modifie :

[assistant] Trois réglages ont été changés sans toi : `double-click 100` (au lieu de 400 — d'où les doubles-clics ratés), `natural-scroll true`, `speed 0.89`. Je cherche le coupable :

[assistant] Aucune commande vocale ni script n'y touche — je n'ai pas trouvé de coupable automatisé. Je remets les valeurs par défaut **et je pose un verrou dconf** pour que plus rien ne puisse les changer :

[assistant] Tout est fait. Récapitulatif honnête :

## Souris — réparée et verrouillée

| Réglage | Valeur trouvée (dérivée) | Maintenant |
|---|---|---|
| `double-click` | **100 ms** — cause des doubles-clics ratés | 400 ms (défaut) |
| `natural-scroll` | true | false (défaut) |
| `speed` | 0,89 | 0,0 (défaut) |
| Accessibilité (clic par survol, clic droit par maintien) | — | désactivés |

**Le « truc » est coupé** : j'ai posé un verrou dconf (`/etc/dconf/db/local.d/locks/souris`) — ces 7 clés sont maintenant en lecture seule, plus aucun script ni panneau ne peut les modifier. Pour le lever un jour : `sudo rm /etc/dconf/db/local.d/locks/souris && sudo dconf update`.

Deux points à savoir :
- **Je n'ai pas identifié le coupable.** Aucun script, hook, autostart ni commande vocale ne touche à ces réglages — j'ai vérifié. Le verrou traite donc le symptôme, pas la cause. S'il bloque quelque chose de légitime, on le saura vite.
- **La souris sans fil YICHIP a disparu de `xinput`** depuis tout à l'heure — le dongle USB semble débranché. Le touchpad ELAN reste actif. Rebranche-le et dis-le-moi si elle ne revient pas.

## Raccourcis — 36 publiés, 5 écartés

Cause racine : ils venaient du profil **M1 (`/home/turbo/…`)**, chemin inexistant ici. J'ai résolu chaque chemin vers l'équivalent local, sinon vers le SSD M1 monté en USB-C (`/media/pamerys/JARVIS-M1`).

Corrigés : icônes et clés SSH M2/M3, profils Remmina, DiskGenius (Wine), Prompt-Library, AnyDesk, profils navigateur Comet/Perplexity, et d

[assistant] D'abord un état des lieux : quels paquets d'entrée sont installés, et y a-t-il une config Xorg parasite qui expliquerait les dérives ?

[assistant] **Coupable trouvé** : `/etc/X11/xorg.conf.d/99-jarvis-mouse-locked.conf`, créé aujourd'hui à 02:06. Je le lis avant de le supprimer :

[assistant] C'est une surcouche JARVIS qui force les options du pointeur au niveau Xorg — ajoutée automatiquement, non standard. Je la désactive et je réinstalle les paquets d'origine :

[assistant] Maintenant je cherche **ce qui a créé ce fichier**, pour l'arrêter à la source :

[assistant] Je reste sur la souris — le protocole d'audit, je le traiterai après (dis-moi si tu veux que je l'implémente).

Réinstallation des paquets d'origine de gestion souris :

[assistant] Réinstallation OK. Je vérifie l'intégrité des fichiers d'origine et je cherche ce qui a créé la config parasite :

[assistant] **Trouvé** : `jarvis-mouse-lock.service` — un service utilisateur actif qui reforce les réglages à chaque démarrage. C'est lui, la source. Je l'inspecte puis je le coupe :

[assistant] C'est coupé. État final :

## Ce qui a été fait

**Paquets d'origine réinstallés** (versions stock Ubuntu 24.04, aucun changement de version) :
`xserver-xorg-input-libinput` · `libinput10` · `libinput-bin` · `xserver-xorg-input-all` · `xinput` · `libevdev2`

**Les trois surcouches JARVIS non standard, coupées** :

| Élément | Action | Réversible par |
|---|---|---|
| `/etc/X11/xorg.conf.d/99-jarvis-mouse-locked.conf` | renommé `.disabled-20260815` | renommer sans le suffixe |
| `jarvis-mouse-lock.service` (utilisateur, actif au démarrage) | `disable --now` + renommé `.disabled-20260815` | `systemctl --user enable` |
| `~/.local/bin/jarvis-mouse-lock` | laissé en place, plus appelé | — |

**Réglages actuels** : tous aux valeurs d'usine (`double-click 400`, `natural-scroll false`, `speed 0.0`, accessibilité désactivée), protégés par le verrou dconf posé plus tôt.

## Deux choses que tu dois savoir

**1. Le script `jarvis-mouse-lock` n'était pas le coupable.** Je l'ai lu : il appliquait justement les *bonnes* valeurs par défaut (400 ms, scroll normal). Ce qui a dérivé — `double-click 100`, `natural-scroll true`, `speed 0.89` — vient d'ailleurs, et **je n'ai pas identifié la source**. Je l'ai quand même coupé comme tu l'as demandé : c'est une couche non standard, et le verrou dconf fait désormais le même travail de façon passive, sans script qui tourne. Si les valeurs redérivent malgré le verrou, ce sera la preuve qu'un processus écrit directement dans dconf — dis-le-moi, je le t

[assistant] Bonne nouvelle pour le touchpad. Je diagnostique la souris secondaire (le dongle sans fil YICHIP) :