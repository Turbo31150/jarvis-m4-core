[user] Tu dépouilles des feuilles de route d'ambulance manuscrites pour reconstituer l'amplitude de travail réelle d'un salarié, dans un contentieux prud'homal côté employeur.

PÉRIMÈTRE : les 6 PDF de JANVIER à JUIN 2025 dans /home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/feuille de route/2025/ (Fdr janv 2025.pdf, Fdr fevr 2025.pdf, Fdr mars 2025.pdf, Fdr Avril 2025.pdf, Fdr Mai 2025.pdf, Fdr Juin 2025.pdf).

MÉTHODE OBLIGATOIRE (scans image pur, sans couche texte — la vision est indispensable) :
1. `pdftoppm -r 150 -png "<fichier.pdf>" /tmp/fdr2025s1/<mois>` (crée le dossier d'abord).
2. Lis CHAQUE image page par page avec l'outil Read. Ne saute aucune page (~15 pages par mois).
3. Tableaux manuscrits de missions : colonnes = chauffeur/équipage, patient, heure de départ, heure d'arrivée, lieux, mention SAMU. Véhicules identifiés par couleur (Violette, Rouge). L'équipage de nuit qui nous intéresse est "SOUF" (Soufiane DRIOUECH) et "JOSH" (Joshua BERNAD).

EXTRACTION — une ligne par MISSION dans /home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/05-CONFIDENTIEL-CONSEIL/FDR-DATA-2025-S1.csv, colonnes :
date;vehicule;equipage;heure_depart;heure_arrivee;lieu_depart;lieu_arrivee;samu_oui_non;page_source;lisibilite
- `lisibilite` = ok | partiel | illisible ; heure illisible = "?" . N'INVENTE JAMAIS une heure.
- Inclus toutes les missions, même d'un autre équipage, en renseignant la colonne equipage.

PUIS une SYNTHÈSE PAR NUIT (nuits où l'équipage inclut SOUF) dans /home/rempc/Bureau/SOL-OPS/Sou

[assistant] I'll start by setting up the working directory and converting the PDFs to images.

[assistant] Layout confirmed and legible. Now I'll dispatch parallel readers, one per month.

[assistant] Scans made 23-24 July 2026 via Genius Scan (mobile), i.e. digitised recently for the litigation. Now waiting on the six month readers.

[assistant] Dépouillement terminé. Deux livrables dans `/home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/05-CONFIDENTIEL-CONSEIL/` : `FDR-DATA-2025-S1.csv` (410 missions) et `FDR-SYNTHESE-2025-S1.md`.

**Volumétrie** — 89 feuilles lues page par page (janv 15, fév 14, mars 16, avr 15, mai 15, juin 14), 410 missions extraites. 89 nuits couvertes sur 181 jours calendaires : 92 nuits sans aucune feuille.

**Lisibilité** — 330 lignes `ok` (80,5 %), 80 `partiel` (19,5 %), 0 illisible. 6 heures de départ et 6 heures d'arrivée manquantes ou illisibles, notées `?` et exclues des calculs. 3 dates de feuille non certaines (fév-07, fév-09, fév-11).

**Amplitudes plancher** (1er départ → dernière arrivée) — moyenne 6h37, médiane 7h15, max 9h50 (24/05), min 0h20 (02/04, feuille dégénérée). 17 nuits avec un trou > 3h. Par mois : janv 6h33 / fév 6h52 / mars 6h27 / avr 6h39 / mai 6h19 / juin 6h55. Les minima extrêmes viennent de feuilles quasi vides et tirent moyenne et médiane vers le bas.

**Le constat central, vérifié sur les 89 feuilles sans exception** : aucune heure de prise ni de fin de service globale — le formulaire pré-imprimé n'en prévoit même pas de case ; aucune signature d'aucune partie ; aucune mention de coupure, repos, pause, repas, permanence ou astreinte. Le document est un relevé de missions, pas un relevé d'heures de travail. Les intervalles sans mission ne peuvent donc pas être qualifiés de pauses.

**Point de vigilance 3 mars** — les feuilles du 03/03 et du 04/03 sont absentes du lot. 