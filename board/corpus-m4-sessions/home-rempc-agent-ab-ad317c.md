[user] Tu dépouilles des feuilles de route d'ambulance manuscrites SCANNÉES (contentieux prud'homal — zéro invention autorisée).

IMAGES À LIRE : /tmp/fdr2025s2/rot/dec-01.png à /tmp/fdr2025s2/rot/dec-16.png (16 pages, déjà redressées).
Tu DOIS lire CHACUNE des 16 images avec l'outil Read (vision). Ne saute AUCUNE page. Lis-les 2 à 3 par message pour rester précis.

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
- `heure_depart` / `heure_arrivee` : format tel qu'écrit (ex 20h40, 00h40, 1h). Si illisible ou vide -> `?`. N'INVENTE JAMAIS UNE 

[user] [Image: original 2100x540, displayed at 2000x514. Multiply coordinates by 1.05 to map to original image.]

[user] [Image: original 2158x960, displayed at 2000x890. Multiply coordinates by 1.08 to map to original image.]

[user] [Image: original 2048x700, displayed at 2000x684. Multiply coordinates by 1.02 to map to original image.]

[user] [Image: original 2090x770, displayed at 2000x737. Multiply coordinates by 1.04 to map to original image.]

[user] [Image: original 2250x875, displayed at 2000x778. Multiply coordinates by 1.13 to map to original image.]

[user] [Image: original 2200x770, displayed at 2000x700. Multiply coordinates by 1.10 to map to original image.]

[user] [Image: original 2880x468, displayed at 2000x325. Multiply coordinates by 1.44 to map to original image.]

[user] [Image: original 2890x442, displayed at 2000x306. Multiply coordinates by 1.45 to map to original image.]

[user] [Image: original 2250x550, displayed at 2000x489. Multiply coordinates by 1.13 to map to original image.]

[assistant] J'ai lu les 16 images (dec-01 à dec-16), avec zooms/recadrages ImageMagick sur les zones douteuses (dates, colonnes SAMU, heures raturées). Fichiers temporaires supprimés, aucun fichier créé.

```
03/12/2025;R;CHRIS/SOUF;20'00;20'20;URG Sete;Dom;montant;dec-01;ok
03/12/2025;R;CHRIS/SOUF;21'00;22'20;URG Lunel;Dom;montant;dec-01;ok
03/12/2025;R;CHRIS/SOUF;1'30;1'40;URG Beziers;Dom;montant;dec-01;ok
03/12/2025;R;CHRIS/SOUF;3'00;3'40;URG Lap;St Eloi;montant;dec-01;ok
?/12/2025;R;CHRIS/SOUF;20'00;20'10;URG Lunel;Dom;montant;dec-02;partiel
?/12/2025;R;CHRIS/SOUF;20'20;20'40;URG Lunel;ehpad;montant;dec-02;partiel
?/12/2025;R;CHRIS/SOUF;21'30;22'10;URG Nimes;Dom;montant;dec-02;partiel
?/12/2025;R;CHRIS/SOUF;0'00;0'40;URG Nimes;Dom;montant;dec-02;partiel
?/12/2025;R;CHRIS/SOUF;2'30;2'50;URG Nimes;Dom;montant;dec-02;partiel
08/12/2025;R;SOUF/CHRIS;20'00;20'40;URG Parc;ehpad;montant;dec-03;ok
08/12/2025;R;SOUF/CHRIS;23'00;23'45;URG Beziers;URG Lap;montant;dec-03;ok
08/12/2025;R;SOUF/CHRIS;1'00;1'15;URG Sete;Dom;montant;dec-03;ok
08/12/2025;R;SOUF/CHRIS;1'40;1'55;URG Sete;Dom;montant;dec-03;ok
08/12/2025;R;SOUF/CHRIS;2'30;2'50;URG Sete;Dom;montant;dec-03;ok
09/12/2025;R;CHRIS/SOUF;20'00;20'25;URG Parc;Dom;montant;dec-04;ok
09/12/2025;R;CHRIS/SOUF;23'00;23'20;URG St Jean;URG Lap;montant;dec-04;ok
10/12/2025;R;CHRIS/SOUF;20'00;20'25;URG GDC;Dom;montant;dec-05;ok
10/12/2025;R;CHRIS/SOUF;21'15;21'25;URG Lunel;ehpad;montant;dec-05;ok
10/12/2025;R;CHRIS/SOUF;23'00;23'25;URG Beziers;Dom;montant