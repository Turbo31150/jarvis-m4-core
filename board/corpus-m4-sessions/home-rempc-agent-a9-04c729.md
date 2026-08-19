[user] Tu dépouilles des feuilles de route d'ambulance manuscrites pour reconstituer l'amplitude de travail réelle d'un salarié, dans un contentieux prud'homal côté employeur.

PÉRIMÈTRE : les 6 PDF de JUILLET à DÉCEMBRE 2025 dans /home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/feuille de route/2025/ (Fdr juillet 2025.pdf, Fdr août 2025.pdf, Fdr sept 2025.pdf, FDR Octobre 2025  (1).pdf, FDR nov 2025.pdf, FDR décembre 2025.pdf).

MÉTHODE OBLIGATOIRE (scans image pur — vision indispensable) :
1. `pdftoppm -r 150 -png "<fichier.pdf>" /tmp/fdr2025s2/<mois>` (crée le dossier d'abord).
2. Lis CHAQUE image page par page avec l'outil Read. Ne saute aucune page (~15 pages/mois).
3. Tableaux manuscrits de missions : équipage, patient, heure de départ, heure d'arrivée, lieux, mention SAMU. Véhicules par couleur (Violette, Rouge). Équipage de nuit ciblé : "SOUF" (Soufiane DRIOUECH) et "JOSH" (Joshua BERNAD).

EXTRACTION — une ligne par MISSION dans /home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/05-CONFIDENTIEL-CONSEIL/FDR-DATA-2025-S2.csv, colonnes :
date;vehicule;equipage;heure_depart;heure_arrivee;lieu_depart;lieu_arrivee;samu_oui_non;page_source;lisibilite
- `lisibilite` = ok | partiel | illisible ; heure illisible = "?" . N'INVENTE JAMAIS une heure.
- Inclus toutes les missions, même d'un autre équipage, en renseignant la colonne equipage.

PUIS une SYNTHÈSE PAR NUIT (nuits où l'équipage inclut SOUF) dans /home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/05-CONFIDENTIEL-CONSEIL/FDR-SYNTHESE-2025-S2.m

[assistant] Structure confirmed. Now I'll fan out the page-by-page vision extraction across the 6 months in parallel, then do the synthesis myself.

[assistant] All six months extracted. Let me verify the two pages reported as unusable, then write the CSV.

[assistant] Confirmed: oct-12 (mean 0.37) and dec-16 (mean 0.23) are dark failed photos, not documents. Now writing the CSV.

[assistant] Livrables écrits :
- `/home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/05-CONFIDENTIEL-CONSEIL/FDR-DATA-2025-S2.csv`
- `/home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/05-CONFIDENTIEL-CONSEIL/FDR-SYNTHESE-2025-S2.md`

**Volumétrie** — 6 PDF, 85 pages converties en images et lues une par une en vision. 83 feuilles exploitables, **374 missions**, **83 nuits**, dont **83 avec SOUF (100 %)**. 2 pages inexploitables (`oct-12`, `dec-16` : clichés flous/noirs, luminance 0,37 et 0,23 contre 0,94 pour une feuille normale — vérifié indépendamment).

**Lisibilité** — 260 lignes `ok` (69,5 %), 114 `partiel` (30,5 %), 0 totalement illisible. Aucune heure inventée : 6 nuits portent au moins une heure en `?`.

**Amplitudes (PLANCHER, pas amplitude de service)** — moyenne 6h27, médiane 7h05, max **10h10 (17/08)**, min 0h20. **22 nuits ≥ 8h**, 4 ≥ 9h, 1 ≥ 10h. Par mois : juil. 13 nuits/50 missions/moy 6h00 · août 17/80/7h04 · sept. 12/49/5h24 · oct. 13/68/6h54 · nov. 13/51/5h43 · déc. 15/76/7h13. **11 nuits avec un trou > 3h** (max 5h10 le 20/07). La moyenne est tirée vers le bas par 8 nuits atypiques (1-2 missions ou aucune mission avant minuit) où la reconstitution est structurellement inopérante.

**Le point le plus fort du dossier** — **aucune des 83 feuilles ne porte d'heure de prise ou de fin de service.** Le formulaire pré-imprimé ne comporte même pas de case pour cela, ni pour coupure, repos, repas ou permanence ; aucune mention manuscrite de ce type sur tout le semestre. **Aucune feuille n'