# VIDÉO DE PREUVE — le livrable prioritaire (verdict table ronde)
Durée cible : 45-60 s. Sans musique. Sans voix off obligatoire. Le terminal parle.

## PLAN DE TOURNAGE (4 plans)
P1 (0-10 s)  — Le cluster existe
   Écran : nvidia-smi, ou la carte des nœuds. On doit VOIR les GPU et leur charge.
P2 (10-25 s) — Ça calcule en local
   Écran : une requête envoyée au modèle local, la réponse qui arrive.
   Incruster le temps de réponse. C'est le chiffre qui frappe.
P3 (25-45 s) — Les agents s'enchaînent seuls
   Écran : le cockpit / les logs, plusieurs tâches qui se déclenchent sans intervention.
P4 (45-55 s) — La preuve du "zéro cloud"
   Écran : couper le réseau externe, relancer la même requête, elle marche quand même.
   >>> C'EST LE PLAN LE PLUS FORT DE LA VIDÉO. Ne pas le sauter.

## CARTON FINAL (3 s)
   "100 % local · 0 cloud · Franck Delmas — Toulouse"

## CAPTURE (prête à lancer)
ffmpeg -f x11grab -s 1920x1080 -i :0.0 -t 60 -r 30 -c:v libx264 -preset fast \
  ~/jarvis/campagnes/linkedin-toulouse-20260818/demo_jarvis.mp4

## RÈGLE
Publier le post AVEC la vidéo. Le post seul = parole. Le post + vidéo = preuve.
Si la vidéo n'est pas prête, le post attend. C'est le verdict du jury.
