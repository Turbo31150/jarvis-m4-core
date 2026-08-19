[user] Tu dépouilles des feuilles de route d'ambulance manuscrites SCANNÉES (contentieux prud'homal — zéro invention autorisée).

IMAGES À LIRE : /tmp/fdr2025s2/rot/juillet-01.png à /tmp/fdr2025s2/rot/juillet-13.png (13 pages, déjà redressées).
Tu DOIS lire CHACUNE des 13 images avec l'outil Read (vision). Ne saute AUCUNE page. Lis-les 2 à 3 par message pour rester précis.

STRUCTURE DE CHAQUE FEUILLE :
- En-tête : `date:` (jj/mm/aa), `Véhicules:` (Rouge ou Violette), `Chauffeurs:` (ex "Josh/Souf")
- Tableau, colonnes : Chauffeurs | Patients | Heures Départ | Heures d'Arrivée | Lieu de Départ | Lieu d'Arrivée | BS+BT OK | Numéro SAMU
- Souvent la colonne "Lieu de Départ" contient "X -> Y" (départ -> arrivée) débordant sur la colonne Lieu d'Arrivée.
- "SOUF" = Soufiane DRIOUECH, "JOSH" = Joshua BERNAD.

CE QUE TU RENVOIES : uniquement des lignes CSV séparées par `;`, une ligne par MISSION remplie :
date;vehicule;equipage;heure_depart;heure_arrivee;lieu_depart;lieu_arrivee;samu_oui_non;page_source;lisibilite

RÈGLES STRICTES :
- `date` : format JJ/MM/2025 tel qu'écrit sur la feuille. Si la date est illisible -> `?`.
- `vehicule` : Rouge | Violette | ? (tel qu'écrit)
- `equipage` : l'en-tête "Chauffeurs:" de la feuille (ex "Josh/Souf"). Normalise en majuscules : JOSH/SOUF, SOUF/JOSH, etc. Si l'en-tête est vide, mets le nom lu dans la colonne Chauffeurs de la ligne.
- `heure_depart` / `heure_arrivee` : format tel qu'écrit (ex 20h40, 00h40, 1h). Si illisible ou vide -> `?`. N'INVENTE JAM

[user] [Image: original 2250x550, displayed at 2000x489. Multiply coordinates by 1.13 to map to original image.]

[user] [Image: original 2340x315, displayed at 2000x269. Multiply coordinates by 1.17 to map to original image.]

[assistant] Les 13 pages ont été lues en vision (avec zooms ciblés sur les cellules douteuses, fichiers temporaires supprimés).

```
date;vehicule;equipage;heure_depart;heure_arrivee;lieu_depart;lieu_arrivee;samu_oui_non;page_source;lisibilite
29/07/2025;Rouge;JOSH/SOUF;20h40;21h;Urg Parc;Dom mtp;montant;juillet-01;ok
29/07/2025;Rouge;JOSH/SOUF;00h40;1h;Urg Lunel;?;montant;juillet-01;partiel
28/07/2025;Rouge;SOUF/JOSH;00h20;1h;Dom Aubais;CH Nimes;oui;juillet-02;partiel
28/07/2025;Rouge;SOUF/JOSH;4h30;4h55;Urg Lunel;Camping GDR;montant;juillet-02;ok
24/07/2025;Rouge;SOUF/LAF;1h;1h25;Urg Sete;Dom Agde;montant;juillet-03;ok
23/07/?;Rouge;SOUF/NEL;00h;1h;URG Nimes CHU;URG LAP;oui;juillet-04;partiel
23/07/?;Rouge;SOUF/NEL;1h55;2h;URG St Privat;Dom ?;montant;juillet-04;partiel
23/07/?;Rouge;SOUF/NEL;3h;3h20;Urg Millenaire;Dom LGM;montant;juillet-04;partiel
20/07/2025;Rouge;SOUF/VAL;20h45;21h10;Urg St Jean;Ehpad Mireval;montant;juillet-05;partiel
20/07/2025;Rouge;SOUF/VAL;2h20;2h45;URG Narbonne;Dom La Palme;montant;juillet-05;partiel
20/07/2025;Rouge;SOUF/VAL;3h05;3h50;URG Narbonne;Dom Fraisse des Corbieres;montant;juillet-05;partiel
19/07/2025;Rouge;SOUF/VAL;20h10;20h45;Urg Privat;CH Bedarieux;montant;juillet-06;ok
19/07/2025;Rouge;SOUF/VAL;21h30;22h15;Urg Lodeve;Urg Lap;montant;juillet-06;ok
19/07/2025;Rouge;SOUF/VAL;22h30;23h;Urg Lap;Ehpad St Andre;montant;juillet-06;ok
19/07/2025;Rouge;SOUF/VAL;23h40;00h20;Urg Lodeve;St Eloi;montant;juillet-06;ok
19/07/2025;Rouge;SOUF/VAL;1h15;1h45;Urg Lap;