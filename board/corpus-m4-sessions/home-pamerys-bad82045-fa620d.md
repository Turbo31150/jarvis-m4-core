[user] <local-command-stdout>CLAUDE_CODE_EFFORT_LEVEL=high overrides effort this session — clear it and ultracode takes over</local-command-stdout>

[assistant] Ça marche. Session opérationnelle, tu peux y aller.

Note : le hook signale `FAILED_SVC:1` (1 service systemd en échec) — tu veux que je regarde lequel ?

[assistant] Ethernet M1 : **échec** (route passe par `10.42.0.1` — tu es en mode hotspot/partage, pas sur le LAN 192.168.1.x). On y reviendra.

D'abord l'écran noir, c'est prioritaire. Je diagnostique avant de réinstaller quoi que ce soit (réinstaller à l'aveugle peut aggraver).

[assistant] GPU OK (NVIDIA 595 répond, `prime on-demand` déjà appliqué). **Problème identifié** : la session active est en `tty` (texte), pas graphique — GDM tourne mais le greeter GNOME ne s'affiche pas. Je creuse la cause exacte avant de toucher aux pilotes.

[assistant] **Cause trouvée** — regarde le `/proc/cmdline` :
```
... ro recovery nomodeset dis_ucode_ldr
```
La machine a **booté en mode recovery + nomodeset**. `nomodeset` désactive le KMS → aucun pilote d'affichage réel → GDM boucle (`on_display_added/removed`), gnome-shell ne démarre jamais = écran noir, et le 2ᵉ écran (DP-1/DP-2) reste inactif.

**Les pilotes ne sont PAS le problème** (NVIDIA 595 répond, Intel présent). Inutile de les réinstaller — c'est l'entrée de boot qui est coincée sur recovery. Je corrige le grubenv :

[assistant] `saved_entry=0` (normal), pas de `next_entry`. Donc le `recovery nomodeset` vient soit de `/etc/default/grub`, soit de l'entrée par défaut modifiée. Je vérifie :

[assistant] **Tout est clair — et bonne nouvelle : rien n'est cassé.**

La config GRUB est correcte :
- `GRUB_DEFAULT=0` → entrée **normale** (ligne 159, KMS actif, pas de nomodeset)
- Le `recovery nomodeset` (ligne 186) est juste l'entrée *recovery*, qui a été **bootée manuellement** au dernier démarrage (probablement pendant le dépannage écran noir précédent).

Donc : les pilotes sont bons, la config est bonne. Il suffit de **rebooter sur l'entrée normale** → KMS réactivé → les 2 écrans + GNOME reviennent. Aucune réinstallation nécessaire (ça aurait été inutile et risqué).

Je force l'entrée normale explicitement et je redémarre :

[assistant] `next_entry=0` armé (entrée normale avec KMS). Je note le diagnostic en mémoire puis je redémarre.

[assistant] La mémoire confirme exactement le diagnostic. Un dernier check avant reboot (fichier xorg OC déjà désactivé ? i915 chargé ?), puis je redémarre :

[assistant] Tout est propre pour un boot normal :
- xorg OC nvidia → déjà désactivé ✓
- Le seul souci = ce boot est en recovery+nomodeset (donc i915 non chargé, c'est normal et temporaire)
- `next_entry=0` armé → le prochain boot chargera KMS → **2 écrans + GNOME reviennent**

Je redémarre maintenant. Ma session va se couper ; **au retour, l'écran doit être normal**. Si le menu GRUB apparaît, ne touche à rien (laisse booter la 1ʳᵉ ligne « Ubuntu »).