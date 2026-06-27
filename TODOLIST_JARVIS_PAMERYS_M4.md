# TODO LIST COMPLÈTE POUR JARVIS M4 (PAMERYS)

## 🚨 URGENT (cette semaine)
- [] **RÉSOLUTION SURCHAUFFE GPU** — *GPU à 87°C, risque de throttling/shutdown* — CLI: `tail -n 100 /home/pamerys/jarvis/logs/thermal-agent.log && bash /home/pamerys/jarvis/scripts/gpu-oc-max.sh --mode=cool`
- [] **PLANIFICATION FINALE ORAL MAMS** — *J-10, structurer les dernières révisions* — CLI: `echo "Créer planning de révision final" | bash /home/pamerys/jarvis/scripts/gemini-ask.sh`
- [] **SIMULATION ORAL BLANC #1** — *S'enregistrer et analyser la prestation* — CLI: `bash /home/pamerys/jarvis/scripts/obs-cours.sh --record --source=webcam --name="MAMS_ORAL_BLANC_1"`
- [] **VÉRIFICATION DOSSIER MDPH 31** — *Deadline imminente, vérifier si pièces manquantes* — CLI: `firefox https://mdphenligne.cnsa.fr/mdph/31`
- [] **SYNCHRONISER BUDGET** — *Valider toutes les transactions de la semaine* — CLI: `python3 /home/pamerys/jarvis/budget/budget_enseignante.py --sync`
- [] **BACKUP COMPLET DU SYSTÈME** — *Créer un snapshot manuel avant le weekend* — CLI: `bash /home/pamerys/jarvis/scripts/backup-daily.sh --force --manual`
- [] **VÉRIFIER L'ÉTAT DES SERVICES CRITIQUES** — *Assurer que le webapp, voice et thermal-agent sont UP* — CLI: `systemctl --user status jarvis-webapp jarvis-voice-widget jarvis-thermal-agent`

## 📅 CONCOURS MAMS (avant 2 juin)
- [] **PRÉPARER LA PRÉSENTATION ORALE** — *Créer/finaliser le support visuel (diaporama)* — CLI: `libreoffice --impress /home/pamerys/Documents/Concours_MAMS/presentation_oral.odp`
- [] **RÉVISER LES FICHES THÉMATIQUES (1-15)** — *Session de révision approfondie* — CLI: `ls /home/pamerys/Documents/Concours_MAMS/fiches/`
- [] **RÉVISER LES FICHES THÉMATIQUES (16-30)** — *Session de révision approfondie*
- [] **SIMULATION ORAL BLANC #2** — *Deuxième tentative avec ajustements* — CLI: `bash /home/pamerys/jarvis/scripts/obs-cours.sh --record --source=webcam --name="MAMS_ORAL_BLANC_2"`
- [] **ANALYSE DES ENREGISTREMENTS** — *Repérer les tics de langage, améliorer la posture* — CLI: `vlc /home/pamerys/Videos/MAMS_ORAL_BLANC_*`
- [] **PRÉPARER LA TENUE POUR L'ORAL** — *Choisir et préparer la tenue vestimentaire*
- [] **CONFIRMER LOGISTIQUE DÉPLACEMENT** — *Vérifier adresse, heure, transport, temps de trajet pour le centre d'examen* — CLI: `firefox "https://www.google.com/maps/dir/domicile/centre_examen_mams"`
- [] **PRÉPARER QUESTIONS POUR LE JURY** — *Préparer 2-3 questions pertinentes à poser en fin d'entretien*

## 🏛️ DÉMARCHES ADMIN
- [] **RELANCER DOSSIER DALO** — *Contacter par email pour suivi du dossier*
- [] **VÉRIFIER PAIEMENTS CAF** — *Se connecter à l'espace personnel pour vérifier les derniers versements* — CLI: `firefox https://www.caf.fr`
- [] **SUIVI DOSSIER LOGEMENT HLM** — *Vérifier l'état de la demande en ligne*
- [] **CONTACTER ACADÉMIE TOULOUSE** — *Envoyer email pour le suivi du dossier administratif enseignant*
- [] **PRENDRE RDV AVEC CAP EMPLOI 31** — *Appeler pour fixer un nouveau point de situation*
- [] **SCANNER ET ARCHIVER NOUVEAUX COURRIERS** — *Numériser tous les documents reçus cette semaine* — CLI: `simple-scan`
- [] **ORGANISER DOSSIER NUMÉRIQUE MDPH** — *Classer tous les documents relatifs à la MDPH dans le dossier dédié* — CLI: `nautilus /home/pamerys/Documents/Admin/MDPH31`

## 💰 BUDGET & FINANCES
- [] **METTRE À JOUR LE BUDGET MENSUEL** — *Intégrer les dernières factures et dépenses* — CLI: `python3 /home/pamerys/jarvis/budget/budget_enseignante.py --update`
- [] **ANALYSER LES POSTES DE DÉPENSES** — *Identifier les catégories les plus dépensières ce mois-ci* — CLI: `python3 /home/pamerys/jarvis/budget/budget_enseignante.py --report`
- [] **PLANIFIER LES DÉPENSES DE JUIN** — *Anticiper les grosses factures à venir*
- [] **VÉRIFIER LE SOLDE DES COMPTES BANCAIRES** — *Synchroniser avec les applications bancaires*
- [] **OPTIMISER LES ABONNEMENTS** — *Lister les abonnements mensuels et évaluer leur utilité*

## 🎓 PÉDAGOGIE & COURS
- [] **PRÉPARER LES COURS DE LA SEMAINE PROCHAINE** — *Créer les supports et plans de cours*
- [] **CORRIGER LES DERNIÈRES ÉVALUATIONS** — *Terminer la pile de copies à corriger*
- [] **RENSEIGNER LES NOTES DES ÉLÈVES** — *Mettre à jour le dashboard avec les nouvelles notes* — CLI: `firefox http://localhost:7777/notes-eleves`
- [] **PRÉPARER LE PROCHAIN CONSEIL DE CLASSE** — *Compiler les moyennes et appréciations*
- [] **CHERCHER DE NOUVELLES RESSOURCES PÉDAGOGIQUES** — *Recherche en ligne de matériel innovant* — CLI: `bash /home/pamerys/jarvis/scripts/recherche.py --query="ressources pédagogiques innovantes pour le primaire"`
- [] **RÉPONDRE AUX EMAILS DES PARENTS D'ÉLÈVES**

## 🤖 SYSTÈME JARVIS
- [] **AUDITER LES LOGS SYSTÈME** — *Rechercher des erreurs récurrentes* — CLI: `python3 /home/pamerys/jarvis/scripts/util_logging.py --find-errors --since=7d`
- [] **METTRE À JOUR LES SCRIPTS JARVIS** — *Pull les dernières modifications depuis le repo Git* — CLI: `cd /home/pamerys/jarvis-linux && git pull && cd -`
- [] **VÉRIFIER L'ESPACE DISQUE** — *Contrôler l'utilisation de /home et /storage* — CLI: `df -h`
- [] **TESTER LA CASCADE LLM** — *Envoyer une requête de test pour vérifier le failover M1->M2->OL1* — CLI: `bash /home/pamerys/jarvis/scripts/lm-ask.sh "Test de la cascade"`
- [] **VÉRIFIER LE STATUT DES BRIDGES** — *Contrôler les ports 9742, 18800, 4173* — CLI: `ss -tuln | grep -E '9742|18800|4173'`
- [] **NETTOYER LE CACHE DE RUFF** — *Libérer de l'espace disque* — CLI: `rm -rf /home/pamerys/jarvis/.ruff_cache`
- [] **REDÉMARRER LE SERVICE OLLAMA** — *Maintenance préventive* — CLI: `systemctl --user restart ollama`
- [] **ARCHIVER LES ANCIENS LOGS** — *Compresser les logs de plus de 30 jours*

## 📱 DASHBOARD & OUTILS
- [] **VÉRIFIER LE FONCTIONNEMENT DES 7 SECTIONS DU DASHBOARD** — *Cliquer sur chaque section pour vérifier l'absence d'erreur 404/500* — CLI: `curl -s -o /dev/null -w "%{http_code}" http://localhost:7777/planning`
- [] **AJOUTER LES PROCHAINS RDV AU CALENDRIER** — *Synchroniser le calendrier avec les nouvelles prises de RDV* — CLI: `firefox http://localhost:7777/calendrier-rdv`
- [] **TESTER L'ASSISTANT IA** — *Poser une question complexe pour tester la pertinence* — CLI: `firefox http://localhost:7777/assistant-ia`
- [] **UPLOADER LES DERNIERS DOCUMENTS SCANÉS** — *Ajouter les courriers administratifs numérisés à la section 'documents'*
- [] **TESTER LE WIDGET VOCAL** — *Dicter une note pour vérifier la retranscription* — CLI: `gnome-sound-recorder`

## 🏠 VIE QUOTIDIENNE
- [] **PLANIFIER LES MENUS DE LA SEMAINE**
- [] **FAIRE LA LISTE DE COURSES**
- [] **PRENDRE RDV CHEZ LE MÉDECIN**
- [] **PLANIFIER UNE SORTIE POUR LE WEEKEND**
- [] **FAIRE LE MÉNAGE DE PRINTEMPS**
- [] **TRIER LES VÊTEMENTS À DONNER**
- [] **APPELER LA FAMILLE**
- [] **LIRE UN CHAPITRE D'UN LIVRE NON-PROFESSIONNEL**
