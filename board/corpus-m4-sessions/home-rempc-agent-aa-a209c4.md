[user] Tu dépouilles des feuilles de route d'ambulance manuscrites scannées (contentieux prud'homal — ZÉRO INVENTION TOLÉRÉE).

FICHIERS : /tmp/fdr2025s1/rot/avril-01.png à /tmp/fdr2025s1/rot/avril-15.png (15 pages, déjà redressées, une page = une nuit).
Lis CHAQUE page avec l'outil Read, dans l'ordre. NE SAUTE AUCUNE PAGE. Une seule image par appel Read.
Si une page apparaît à l'envers, exécute `convert /tmp/fdr2025s1/rot/<nom>.png -rotate 180 /tmp/fdr2025s1/rot/<nom>-r180.png` puis relis.

STRUCTURE DE CHAQUE FEUILLE :
- En-tête : "Date:" (jj/mm/aa) | "Véhicules:" (ex. Violette, Rouge) | "Chauffeurs:" (ex. SOUF/JOSH)
- Tableau : Chauffeurs | Patients | Heures Départ | Heures d'Arrivée | Lieu de Départ | Lieu d'Arrivée | BS+BT OK | Numéro SAMU
- Marge gauche : petits chiffres rouges (km probables). Colonne "Numéro SAMU" : parfois un numéro, parfois des montants € rouges ajoutés après coup.
- L'équipage de nuit surveillé = "SOUF" (Soufiane DRIOUECH) et "JOSH" (Joshua BERNAD).

CE QUE TU DOIS RENVOYER — DEUX BLOCS :

BLOC 1 = lignes CSV, séparateur `;`, une ligne PAR MISSION (toutes missions, tous équipages), sans en-tête :
date;vehicule;equipage;heure_depart;heure_arrivee;lieu_depart;lieu_arrivee;samu_oui_non;page_source;lisibilite
- `date` : format AAAA-MM-JJ tel qu'écrit sur la feuille.
- `vehicule` : ce qui est écrit après "Véhicules:" (Violette / Rouge / autre / "?" si vide).
- `equipage` : le contenu de la colonne "Chauffeurs" de CETTE ligne (ex. JOSH, SOUF, ou autre nom). Si v

[user] [Image: original 2057x1281, displayed at 2000x1246. Multiply coordinates by 1.03 to map to original image.]

[assistant] J'ai lu les 15 pages, dans l'ordre, aucune n'était à l'envers (aucune rotation nécessaire).

## BLOC 1 — CSV (une ligne par mission)

```
2025-04-30;Rouge;JOSH;20h30;20h50;URG Mil;Dom Mtp;montant;avril-01;ok
2025-04-30;Rouge;JOSH;22h15;22h35;URG Béziers;Dom Montady;montant;avril-01;ok
2025-04-30;Rouge;JOSH;23h10;23h40;URG Béziers;Dom Fouzilhon;montant;avril-01;ok
2025-04-30;Rouge;SOUF;1h00;1h30;URG Béziers;EHPAD Fontes;montant;avril-01;ok
2025-04-30;Rouge;SOUF;3h;3h10;Urg Lunel;Dom Lunel;non;avril-01;partiel
2025-04-30;Rouge;SOUF;3h25;3h30;Dom Lunel;Urg Lunel;montant;avril-01;partiel
2025-04-27;Rouge;SOUF;20h30;20h55;URG Mil;EHPAD LGM;montant;avril-02;ok
2025-04-27;Rouge;JOSH;23h30;00h30;URG Narbonne;URG LAP;montant;avril-02;ok
2025-04-27;Rouge;SOUF;1h30;1h45;URG Béziers;Dom Lignan;montant;avril-02;ok
2025-04-27;Rouge;SOUF;2h00;2h30;URG Béziers;Dom Vias;montant;avril-02;ok
2025-04-27;Rouge;SOUF;3h00;3h30;URG Béziers;Dom Bessan;montant;avril-02;ok
2025-04-27;Rouge;SOUF/JOSH;?;?;CH GDR;URG Nimes;montant;avril-02;partiel
2025-04-26;Rouge;SOUF;20h10;20h40;URG Nimes;Dom Vauvert;montant;avril-03;ok
2025-04-26;Rouge;SOUF;22h00;22h30;URG Sète;Dom Mèze;montant;avril-03;ok
2025-04-26;Rouge;SOUF;23h30;00h10;URG St Privat;EHPAD Aspiran;montant;avril-03;ok
2025-04-26;Rouge;JOSH;2h00;2h10;URG LAP;St Elois;montant;avril-03;ok
2025-04-26;Rouge;JOSH;3h15;3h30;UTEC;St Elois HGEA;montant;avril-03;ok
2025-04-25;Rouge;JOSH;20h30;21h00;URG Lunel;Parc;montant;avril-04;ok
2025-04-25;Rouge;JOSH;22h45