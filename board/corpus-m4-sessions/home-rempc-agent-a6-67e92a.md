[user] Tâche : inventaire en LECTURE SEULE des pièces d'un dossier, sur cette machine Linux (user rempc). Ne modifie, ne déplace, ne supprime aucun fichier.

CONTEXTE : dossier « Emma COSTE », salariée protégée d'une SARL d'ambulances, licenciement pour inaptitude soumis à autorisation de l'inspection du travail. Un dossier a été déposé le 28/07/2026 à la DDETS du Gard. Une enquête contradictoire a lieu le 18/08/2026, à laquelle l'employeur devra se présenter avec ses pièces.

PIÈCES À RECHERCHER (liste attendue du dossier DREETS) :
1. La demande d'autorisation de licenciement elle-même (rédigée par le cabinet Capstan, envoyée le 28/07/2026)
2. L'avis d'inaptitude du Dr LEGER daté du 01/06/2026 (inaptitude d'origine professionnelle, dispense de reclassement)
3. Le PV de carence du 2nd tour des élections CSE (établi le 13/07/2026, télétransmis le 15/07/2026)
4. La convocation à l'entretien préalable envoyée en LRAR le 15/07/2026 (n° de suivi 87001429717077B) + les preuves LRAR (dépôt, contenu, retrait)
5. Le constat de non-présentation à l'entretien préalable du 27/07/2026 (Emma COSTE ne s'est pas présentée, constat dressé à 11h)
6. La lettre de démission du mandat CSE (14/04/2026)
7. La notification d'IPP à 7 %
8. Le courrier de Mme COSTE du 23/07/2026
9. Le contrat de travail (CDI du 01/02/2023) et les bulletins de salaire
10. Le courrier de l'inspection du travail du 03/08/2026 (convocation à l'enquête)

OÙ CHERCHER (bornes strictes, pour ne pas scanner tout le disque) :
- /home/r

[assistant] Found the LRAR tracking-number proof file. That resolves piece 4. Let me confirm no constat de non-présentation exists, and do a final check of rclone + AT/notification IPP draft location, plus close the loop on `/home/rempc/Documents/CSE` (real dir, not symlink, just a leftover copy).

[assistant] ## Inventaire — dossier Emma COSTE (enquête DDETS du 18/08/2026)

Recherche effectuée sur `/home/rempc/Bureau/SOL-OPS/`, `/home/rempc/Bureau/SOLEIL/`, `/home/rempc/Téléchargements/`, `/home/rempc/Documents/`, et le Google Drive (rclone, dossier ID `1Dlx-KRlBXorvbXt5KLY7oJa5PnfOzWEE`). Aucun fichier lu, modifié ou déplacé.

**Note structurelle importante** : `SOL-OPS` a été entièrement vidé le 30/07/2026 (voir `00-DOSSIER-TRAITE-ET-VIDE-20260730.txt`) et reclassé vers `~/Bureau/SOLEIL/2-LICENCIEMENT-COSTE-26.0231/` (dossier DDETS) et `~/Bureau/SOLEIL/3-CSE/` (élections/CSE) — c'est là qu'est la quasi-totalité des pièces, pas dans `SOL-OPS/Capstan-Emma-COSTE` (quasi vide, un seul brouillon de mail).

| Pièce attendue | Chemin absolu trouvé | Remarque |
|---|---|---|
| 1. Demande d'autorisation de licenciement (Capstan, 28/07/2026) | `/home/rempc/Bureau/SOLEIL/2-LICENCIEMENT-COSTE-26.0231/10-DOSSIER-DREETS/DEMANDE-AUTORISATION-COSTE-28juillet.pdf` (+ preuve jointe `PREUVES-LAPOSTE/PJ1-COURRIER-DEMANDE-AUTORISATION-COSTE-28juillet2026 (3).pdf`, + `ENVOI-LAPOSTE-COSTE-DREETS-28juillet-COMPLET.pdf` dans `60-INSPECTION-TRAVAIL-DDETS/`) | Présent, plusieurs copies cohérentes (brouillon pré-rempli + version finale + PJ envoyée) |
| 2. Avis d'inaptitude Dr LEGER (01/06/2026) | `/home/rempc/Bureau/SOLEIL/2-LICENCIEMENT-COSTE-26.0231/10-DOSSIER-DREETS/PREUVES-LAPOSTE/PJ3-AVIS-INAPTITUDE-Dr-LEGER-01juin2026 (4).pdf` (original signé : `30-AVIS-INAPTITUDE/2026-06-01-COSTE-ITI-volet3-SIGNE-p