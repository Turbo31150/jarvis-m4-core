[user] Tu dépouilles des feuilles de route d'ambulance manuscrites pour reconstituer l'amplitude de travail réelle d'un salarié, dans un contentieux prud'homal côté employeur.

PÉRIMÈTRE : les 6 PDF de 2026 dans /home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/feuille de route/2026/ (FDR janv 2026.pdf, FDR fev 2026.pdf, FDR mars 2026.pdf, Fdr Avril 2026.pdf, Fdr Mai 2026.pdf, Fdr juillet 2026.pdf).

MÉTHODE OBLIGATOIRE (scans image pur — vision indispensable) :
1. `pdftoppm -r 150 -png "<fichier.pdf>" /tmp/fdr2026/<mois>` (crée le dossier d'abord).
2. Lis CHAQUE image page par page avec l'outil Read. Ne saute aucune page (~15 pages/mois).
3. Tableaux manuscrits de missions : équipage, patient, heure de départ, heure d'arrivée, lieux, mention SAMU. Véhicules par couleur (Violette, Rouge). Équipage de nuit ciblé : "SOUF" (Soufiane DRIOUECH) et "JOSH" (Joshua BERNAD).

EXTRACTION — une ligne par MISSION dans /home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/05-CONFIDENTIEL-CONSEIL/FDR-DATA-2026.csv, colonnes :
date;vehicule;equipage;heure_depart;heure_arrivee;lieu_depart;lieu_arrivee;samu_oui_non;page_source;lisibilite
- `lisibilite` = ok | partiel | illisible ; heure illisible = "?" . N'INVENTE JAMAIS une heure.
- Inclus toutes les missions, même d'un autre équipage, en renseignant la colonne equipage.

PUIS une SYNTHÈSE PAR NUIT (nuits où l'équipage inclut SOUF) dans /home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/05-CONFIDENTIEL-CONSEIL/FDR-SYNTHESE-2026.md :
date | nb missions | 1re prise en c

[assistant] The pages are legible after rotation. Now I'll dispatch one agent per month to read every page.

[assistant] Both spot-checks match the agents' readings exactly (avril-11: arrival 23h35 before departure 23h45 confirmed; mars-07: sheet genuinely truncated in the source PDF). Deliverables written.

**Fichiers produits**
- `/home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/05-CONFIDENTIEL-CONSEIL/FDR-DATA-2026.csv` — 355 missions, 10 colonnes
- `/home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/05-CONFIDENTIEL-CONSEIL/FDR-SYNTHESE-2026.md` — synthèse par nuit + totaux mensuels + anomalies

**Volumétrie** — 6 PDF, 74 pages lues une par une (vision, 150→300 dpi, rotation −90°), 74 nuits, 355 missions (4,9/nuit). Équipage nominatif : SOUF 152, JOSH 130, CHRIS 13, non renseigné 60 (16,9 %).

**Lisibilité** — 228 lignes `ok` (64,2 %), 127 `partiel` (35,8 %), 0 illisible. 15 champs horaires sur 710 non exploitables (2,1 %), notés `?` et exclus des calculs — aucune heure déduite.

**Amplitudes (PLANCHER, pas amplitude de service)** — 1re prise en charge → dernière fin. Toutes nuits : moyenne 7h04, médiane 7h50, max 10h30 (21/03), min 0h30. Sous-ensemble de contrôle (nuits ≥ 4 missions, n=53, le plus défavorable à l'employeur) : moyenne 8h04, médiane 8h00, max 10h30. Seulement 4 nuits ≥ 10h ; 38/73 nuits < 8h. 12 nuits avec un trou > 3h sans mission, jusqu'à 6h45 (01/05).

**Réserve n°1** — aucune des 74 feuilles ne porte d'heure de prise ni de fin de service : le formulaire n'en prévoit pas de case, et rien n'a été ajouté à la main. Aucune mention de coupure, repos, repas, pause, permanence ou astreint