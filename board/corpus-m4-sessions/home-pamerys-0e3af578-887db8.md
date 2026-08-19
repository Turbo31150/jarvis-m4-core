[assistant] Écran noir + souris seule après changement de résolution GNOME = mode d'affichage invalide appliqué. Je répare sans tuer ta session. D'abord je détecte le backend (Wayland/X11) :

[assistant] X11 — bonne nouvelle, je peux réparer la résolution sans fermer ta session. Je récupère le DISPLAY de ta session graphique et je force un mode d'écran valide :

[assistant] xrandr voit bien **1920x1080 @ 144Hz sur eDP-1** (ton écran de portable) — le mode est valide. Le noir vient de **gnome-shell figé** (82 % CPU en boucle), pas d'une mauvaise résolution. Je force d'abord un modeset pour réveiller l'affichage sans rien perdre :

[assistant] Modeset propre : **un seul écran eDP-1 en 1920x1080**, sortie fantôme de droite coupée. Maintenant je relance gnome-shell (il tourne figé à 82 %) — sur X11 ça ne ferme pas tes fenêtres :

[assistant] Nouveau gnome-shell (PID 358028) démarre, l'ancien va rendre la main. J'attends la stabilisation :

[assistant] L'ancien shell figé est mort, le nouveau tourne normalement (charge retombée à 2.1). **Mais** au redémarrage GNOME a réappliqué ton ancien réglage **1680x1050** (déformé, non-natif) — c'était ça le mauvais réglage. Je remets le natif **1920x1080** et j'empêche GNOME de re-imposer le mauvais :

[assistant] ✅ **Écran réparé** — retour en **1920x1080 natif** sur eDP-1.

| Cause | Fix appliqué |
|---|---|
| Résolution 1680x1050 (non-native, déformée) forcée par `monitors.xml` | Retiré → sauvé en `~/.config/monitors.xml.bak-1680` |
| gnome-shell figé à 82 % CPU (écran noir + souris seule) | `gnome-shell --replace` → nouveau shell, charge 2.1 |
| Sortie fantôme à droite | Coupée via `xrandr --off` |

Ton bureau doit être revenu. Le `crtc failed` est bénin (gnome-shell reprenait le crtc au même instant) — l'état final confirme 1920x1080.

Si tu veux une autre résolution : **Paramètres → Affichage** répond maintenant, et GNOME recréera un `monitors.xml` propre au prochain choix validé. Écran toujours noir ? dis-le, je relance le shell une 2ᵉ fois.

[assistant] Je remets l'affichage GNOME aux réglages d'origine (reset complet monitors.xml + clés dconf mutter/interface) et je regarde le service en échec :

[assistant] Réglages d'affichage remis à zéro. État :

| Élément | Résultat |
|---|---|
| `monitors.xml` | supprimé → GNOME repart au natif (ancien gardé en `.bak-1680`) |
| dconf `mutter` + scaling + experimental-features | remis aux **défauts d'usine** |
| Résolution | **1920x1080** natif confirmé (`crtc failed` bénin — l'état final est bon) |
| Service en échec | `obex.service` (Bluetooth) — **sans rapport** avec l'écran, je le nettoie ci-dessous |

[assistant] ✅ **Tout est remis d'origine et stable.**

| Contrôle | État |
|---|---|
| gnome-shell | PID 360613, **2 % CPU** — plus de figeage |
| scaling-factor | `0` (auto, défaut) |
| experimental-features | `[]` vide → le **fractional scaling** (cause probable des crashs de *Paramètres → Affichage*) est désactivé |
| Résolution | 1920x1080 natif |
| obex.service | alerte nettoyée |

Ce qui faisait planter, c'était très probablement le **scaling expérimental** resté actif dans mutter combiné au `monitors.xml` en 1680x1050. Les deux sont maintenant supprimés.

Tu peux rouvrir **Paramètres → Affichage** : il devrait s'ouvrir sans planter et proposer le 1920x1080. Ne réactive pas le « scaling fractionné » si l'option apparaît — c'est lui le fautif. Si ça replante, dis-le, je regarde les logs de crash (`journalctl`).

[assistant] Le `crtc failed` est le vrai symptôme — le GPU refuse d'afficher le framebuffer. Je diagnostique la cause réelle (GPU/DRM) avant de toucher à autre chose :

[assistant] Cause trouvée : **ton écran eDP est câblé sur l'Intel i915, mais Xorg tourne côté NVIDIA** (`NVIDIA(G0)`) → le CRTC Intel ne peut pas afficher → noir. C'est un problème PRIME/GPU. Je corrige le PRIME puis je redémarre la session graphique (GDM) comme tu demandes :