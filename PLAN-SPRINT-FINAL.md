# PLAN SPRINT FINAL — JARVIS PAMERYS M4
# Date: 2026-05-23 | Oral MAMS: J-10

## TASK-F1: Réparer et consolider jarvis-voice-widget
- Vérifier pourquoi le service est inactif (journalctl --user -u jarvis-voice-widget)
- Corriger le problème (dépendance manquante, port occupé, etc.)
- Redémarrer et valider le statut: systemctl --user status jarvis-voice-widget
- Vérifier: Alt+X doit déclencher la capture vocale

## TASK-F2: Script audit-jarvis.sh — audit complet en 1 commande
Créer ~/jarvis/scripts/audit-jarvis.sh qui vérifie:
- Services systemd (webapp/voice-widget/thermal-agent/multiagent)
- Cluster LLM M1/M2 (ping + /v1/models)
- GPU temp depuis thermal-status.json
- Espace disque (/ et /home)
- Ports clés (7777, 1234)
- SQLite DBs integrity (budget.db, todo.db, notes.db)
- Git repos (jarvis + machine-m4-pamerys) status
- Résumé: SCORE /10 avec items OK/KO
Symlink: /usr/local/bin/audit-jarvis

## TASK-F3: Planning révision MAMS jusqu'au 2 juin
Créer ~/jarvis/scripts/mams-planning.py:
- Calcule les jours restants (J-10 au J-1)
- Assigne un thème par jour depuis mams_questions_jury.json
- J-10 (23/05): Parcours professionnel + posture
- J-9 (24/05): Fonction publique + statut
- J-8 (25/05): Comptabilité + finances
- J-7 (26/05): Gouvernance EPLE
- J-6 (27/05): Politiques éducatives + actualités
- J-5 (28/05): Mises en situation management
- J-4 (29/05): Révision globale + simulation orale
- J-3 (30/05): Réponses-type + reformulation
- J-2 (01/06): Simulation finale + logistique
- J-1 (01/06 soir): Relecture + repos
Affiche le programme du jour + questions du thème du jour
Symlink: /usr/local/bin/mams-planning

## TASK-F4: Intégrer tout dans le dashboard web (section Système)
Ajouter dans /api/system (nouveau endpoint) :
- Statut de tous les services
- Score audit (calculé dynamiquement)
- J-X MAMS
Mettre à jour la section Système du dashboard pour afficher ces infos en temps réel
