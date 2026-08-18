# Prospection — etat reel du pipeline (2026-08-15)

## A QUOI CA SERT
Savoir qui a ete contacte, par quel canal, avec quel resultat. Repondre a :
qui relancer, quelles adresses sont mortes, quels canaux ne sont pas exploites,
pourquoi un envoi a echoue, quel segment reste a traiter.

## VOLUMES MESURES
- contacts moissonnes : 450
- vivier qualifie : 48
- envois reels : 15 dont 1 rebond(s)
- contacts verifies stricts : 141
- FORMULAIRE_SECURISE : 100
- VERIFIE_HTML_DIRECT : 41

## SEGMENTS DU VIVIER
- segment A priorite 1 : 14 contact(s)
- segment B priorite 2 : 10 contact(s)
- segment B priorite 3 : 1 contact(s)
- segment C priorite 3 : 19 contact(s)
- segment X priorite 2 : 4 contact(s)

## ENVOIS EFFECTUES (14/08/2026)
- Aura Aero — Recherche documentaire en réseau isolé — pack Dossier technique confidentiel — ENVOYE
- Barreau de Toulouse — Analyse de pièces sans transfert de données — pack Data-Room — ENVOYE
- CS Group Occitanie — Socle IA sur site en marque blanche — pack Veille & appel d'offres — ENVOYE
- Eviden / Atos Toulouse — Socle IA sur site en marque blanche — pack Veille & appel d'offres — ENVOYE
- Evotec France — Recherche documentaire sans sortie de données — pack Documentation reglementaire — ENVOYE
- GTP Bioways — Recherche documentaire sans sortie de données — pack Documentation reglementaire — REBOND
- Hemeria — Recherche documentaire en réseau isolé — pack Dossier technique confidentiel — ENVOYE
- In Extenso Finance Occitanie — Analyse de pièces sans transfert de données — pack Data-Room — ENVOYE
- IRDI Capital Investissement — Analyse de pièces sans transfert de données — pack Data-Room — ENVOYE
- MBA Capital Toulouse — Analyse de pièces sans transfert de données — pack Data-Room — ENVOYE
- Midi 2i — Analyse de pièces sans transfert de données — pack Data-Room — ENVOYE
- Naval Group — Recherche documentaire en réseau isolé — pack Dossier technique confidentiel — ENVOYE
- Sogeclair Aerospace — Recherche documentaire en réseau isolé — pack Dossier technique confidentiel — ENVOYE
- Sopra Steria Toulouse — Socle IA sur site en marque blanche — pack Veille & appel d'offres — ENVOYE
- Thales Alenia Space France — Recherche documentaire en réseau isolé — pack Dossier technique confidentiel — ENVOYE

## PROBLEMES CONSTATES
- 5 entreprises ont recu le meme message DEUX fois a ~6 min d'ecart (Aura Aero, Barreau de Toulouse, CS Group, Eviden, Evotec).
- 1 adresse morte : rebond serveur 'adresse introuvable'.
- 123 formulaires officiels moissonnes, AUCUN exploite a ce jour.
- La garde anti-renvoi filtre sur statut='ENVOYE' : un contact passe en REBOND n'est plus filtre et repartirait.
- Les contacts nominatifs des grands comptes viennent des pages presse : ce sont des attaches de presse, pas des acheteurs.
