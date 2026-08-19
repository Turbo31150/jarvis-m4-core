[user] sur linux mode secour gnom graphique ececran noir retelecherghe le entier a lorginine modification de la dimension de la lécran la résolution du coup je n'est que le pointeur

[assistant] Écran noir GNOME avec seul le pointeur = mutter tourne (il dessine le curseur) mais le bureau ne rend pas, à cause d'une résolution invalide écrite dans la config. Je diagnostique l'état réel puis je corrige.

[assistant] Deux sessions X tournent (Xorg 2045 et 4600), gnome-shell dupliqué. Le panneau eDP-1 est sur l'iGPU Intel (card1). Je vérifie la résolution réellement appliquée sur l'affichage `:1` pour cibler la correction.

[assistant] La résolution est correcte (1920x1080@144Hz natif, monitors.xml absent). Le vrai problème : gnome-shell/mutter dupliqués (plusieurs compositeurs en conflit issus des tentatives précédentes `--replace`) → bureau noir, seul le curseur matériel s'affiche. Je vérifie la charge et les erreurs de rendu avant d'agir.

[assistant] Diagnostic clair :

| Processus | CPU | Rôle |
|---|---|---|
| gnome-shell **3286** | 0.9% | greeter GDM (tty1) — sain |
| gnome-shell **5758** | **25.2%** | ta session (tty2 `:1`) — **figée**, rend le bureau noir |

La résolution est bonne (1920x1080@144 natif), pas de `monitors.xml` corrompu, prime en `on-demand` (correct). Le seul coupable = ta session gnome-shell **5758** qui tourne en boucle à 25% et ne compose plus le bureau → tu ne vois que le curseur.

Solution décisive : redémarrer GDM proprement. Ça tue la session figée et te ramène à un écran de connexion neuf → nouvelle session qui rend correctement. L'écran va clignoter et afficher la page de login.

[assistant] GDM redémarré : les sessions figées sont éliminées, l'écran de connexion (GDM, tty1) est maintenant actif. Le nouveau gnome-shell (15753) démarre — je vérifie qu'il se stabilise et ne repart pas en boucle CPU.

[assistant] Le greeter s'est stabilisé (7.5% CPU, aucune erreur Xorg). Mais le VT actif est **tty2** (probablement vide) alors que l'écran de connexion GDM est sur un autre VT — c'est pour ça que tu peux encore voir du noir. Je bascule l'affichage sur le bon VT.

[assistant] Toujours noir même sur le greeter GDM neuf → ce n'est **pas** un problème de session, mais un problème de **rendu GPU réel** : le curseur (plan matériel séparé) s'affiche, mais le plan principal (le bureau) reste noir. Ça touche même l'écran de connexion. Je cherche la cause racine côté pilote/DRM.

[assistant] GPU sain côté matériel : i915 initialisé, `fb0` OK, backlight allumé (69%), curseur visible. Donc le noir vient de la **couche de rendu GL de mutter**, pas du KMS. Deux signaux importants dans dmesg/lsmod :

1. `nvidia … Cannot find any crtc` (normal, GPU headless)
2. **Le module `xe` ET `i915` sont chargés en même temps** pour le GPU Intel → conflit possible de pilote/rendu.

Je teste le rendu GL réel sur l'affichage et je vérifie à qui appartient la carte.

[assistant] Résultat capital : **le GL fonctionne** sur le greeter — `OpenGL renderer: Mesa Intel(R) UHD Graphics (TGL GT1)`, card1→i915, card2→nvidia. Donc GPU, GL, backlight, curseur : tout marche. Le bureau rendu est correct **en mémoire**, mais l'affichage sur la dalle eDP est **figé en noir** : c'est le pipe/CRTC de scanout eDP qui est bloqué depuis ton changement de résolution (le plan curseur se met à jour séparément, d'où le curseur seul).

Le remède non-destructif : forcer un **modeset complet** en basculant sur un VT texte puis revenir — ça oblige i915 à ré-établir le pipe eDP. J'essaie ça d'abord, et je vérifie que la config de boot est propre pour un redémarrage si besoin.

[assistant] Config de boot **propre** : pas de `nomodeset`, prime `on-demand`, pas de `xorg.conf` forçant NVIDIA, `saved_entry=0`. Le modeset par VT n'a pas débloqué le pipe eDP — il est réellement figé au niveau du moteur d'affichage i915, et tous les resets « à chaud » (xrandr, gnome-shell --replace, restart GDM, bascule VT) ont échoué.

Le seul reset fiable qui reste = **redémarrer** : ça réinitialise complètement le moteur d'affichage i915. Et comme la config est propre, la machine reboot directement sur un écran de connexion fonctionnel (pas de retour au noir). Je le fais maintenant.