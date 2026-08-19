[user] MACHINE : pamerys-m4 (portable), uid=1000(pamerys), Ubuntu, GNOME sur WAYLAND (session 3, seat0, tty2).
GPU     : Intel UHD (i915, PCI 00:02.0, card1) = GPU D'AFFICHAGE. NVIDIA RTX 3050 Mobile (01:00.0, card2) = calcul.
ÉCRANS  : card1-eDP-1 CONNECTÉ (interne, 1920x1080) ET card1-HDMI-A-1 CONNECTÉ (externe). DP-1, HDMI-A-2, DP-2, DP-3 déconnectés.
SYMPTÔME SIGNALÉ PAR L'UTILISATEUR : "la résolution n'arrête pas de changer" (toute seule, de façon répétée).
INDICES DÉJÀ TROUVÉS :
  - journalctl : "août 18 07:48:17 pamerys-m4 kernel: i915 0000:00:02.0: Using 39-bit DMA addresses"
    => le module i915 a été (re)chargé à 07:48 alors que la session tournait.
  - journalctl : "août 18 07:45:41 sudo[1477240] pamerys : PWD=/home/pamerys/labo/bibliotheque/series ;
    USER=root ; COMMAND=/usr/bin/fuser -v /dev/nvidia0 /dev/nvidiactl /dev/nvidia-modeset /dev/nvidia-uvm /dev/nvidia-uvm-tools"
    => un script manipulait les devices NVIDIA juste avant.
  - nvidia-smi renvoie "Failed to initialize NVML: Driver/library version mismatch" (NVML library version: 595.84).
  - Les symlinks /sys/class/drm/card1-* datent de 08:41, card2-DP-3 de 02:02 (recréations successives).

RÈGLE ABSOLUE : DIAGNOSTIC EN LECTURE SEULE. N'exécute AUCUNE commande qui modifie l'état :
pas de modprobe, pas de systemctl start/stop/restart, pas de kill, pas de xrandr/wlr-randr qui change un mode,
pas d'écriture de fichier, pas d'apt, pas de sudo modifiant quoi que ce soit.
Lecture seule uniquement : cat, ls, grep, f

[assistant] I'll investigate the JARVIS ecosystem for code touching display/GPU modules. Starting with parallel read-only scans.

[assistant] Beaucoup de bruit dans les archives. Je cible les scripts réellement exécutables et actifs.

[assistant] Processus clé identifié : `gpu_guardian.py` tourne depuis 6h42. Je l'examine ainsi que les scripts GPU de `series`.

[assistant] Message "Try one of the following resolutions" en masse. Je remonte au contexte complet.

[assistant] Le message "resolutions" vient de pynput (faux ami). Mais j'ai trouvé une tempête de processus. Je vérifie son déclencheur.