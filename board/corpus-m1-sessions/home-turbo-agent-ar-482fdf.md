[assistant] Bon, environnement confirmé : GNOME Shell 46.0, Pillow 10.2.0, sox, ffmpeg, 4 GPU. Aucune trace de wallpaper/hud/indicator dans les services actifs. Je passe à la construction des 3 couches manquantes.

[assistant] Le générateur fonctionne. Maintenant les units systemd user (service oneshot + timer 5min).

[assistant] 6 WAV générés et validés. Recâblons les autostarts existants (chemins cassés) pour pointer vers ces nouveaux fichiers, et testons la lecture réelle.