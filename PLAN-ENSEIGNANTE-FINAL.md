# JARVIS PAMERYS M4 — Plan final système enseignante
## Contexte
Machine: ASUS TUF F15, Ubuntu 24.04, user=pamerys, enseignante
Services actifs: jarvis-thermal-agent, jarvis-voice-widget, jarvis-multiagent
Déjà fait: budget, planning, recherche, contenu, dock, thème, window-arrange

## TASK-A: Dashboard terminal journalier (~/jarvis/scripts/dashboard.py)
Script qui s'affiche au démarrage du terminal — résumé de la journée:
- Heure, météo locale (wttr.in via curl)
- Planning du jour (planning.py aujourd'hui)
- Rapport budget rapide (budget.py rapport --compact)
- Statut cluster M1/M2 (ping rapide)
- GPU/CPU temp depuis thermal-status.json
- Citations pédagogiques aléatoires (liste intégrée)
Lancer automatiquement via ~/.bashrc : `python3 ~/jarvis/scripts/dashboard.py`

## TASK-B: Sauvegarde automatique quotidienne (cron)
Créer ~/jarvis/scripts/backup-daily.sh :
- Sauvegarde ~/Documents/ vers ~/Backups/docs-YYYY-MM-DD.tar.gz (max 7 jours)
- Sauvegarde SQLite: budget.db, planning.db, jarvis_master.db
- Push BASE-SQL3 si modifié
- Notification GNOME à la fin
Cron: `0 22 * * * bash ~/jarvis/scripts/backup-daily.sh`

## TASK-C: Script notes élèves automatisé (~/jarvis/scripts/notes_eleves.py)
- CLI: notes_eleves.py ajouter --nom "Dupont" --prenom "Jean" --classe "3A" --matiere "Maths" --note 14 --coeff 2
- notes_eleves.py moyenne --classe "3A" --matiere "Maths"
- notes_eleves.py bulletin --nom "Dupont" → génère un résumé texte
- Stockage SQLite ~/jarvis/notes.db
- Export CSV vers ~/Documents/Eleves/Notes/

## TASK-D: Service OBS auto-record pour cours (~/jarvis/scripts/obs-cours.sh)
- Lance OBS en mode headless avec profil "cours"
- Enregistre dans ~/Documents/Contenu/Videos-cours/YYYY-MM-DD_[titre].mkv
- Compresse après enregistrement avec ffmpeg (H.264 CRF 23)
- Commande: obs-cours.sh start [titre] / obs-cours.sh stop

## TASK-E: Push GitHub tout en une commande (~/jarvis/scripts/push-all.sh)
- Vérifie que widget, thermal-agent, multiagent sont actifs
- Backup SQL rapide
- Push BASE-SQL3
- Push machine-m4-pamerys
- Affiche résumé
Alias: `push-all`
