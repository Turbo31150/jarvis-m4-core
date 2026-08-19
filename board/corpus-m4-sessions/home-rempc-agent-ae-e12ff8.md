[user] Tu dépouilles des feuilles de route d'ambulance manuscrites SCANNÉES (contentieux prud'homal — zéro invention autorisée).

IMAGES À LIRE : /tmp/fdr2025s2/rot/nov-01.png à /tmp/fdr2025s2/rot/nov-15.png (15 pages, déjà redressées).
Tu DOIS lire CHACUNE des 15 images avec l'outil Read (vision). Ne saute AUCUNE page. Lis-les 2 à 3 par message pour rester précis.

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

[user] [Image: original 2109x1241, displayed at 2000x1177. Multiply coordinates by 1.05 to map to original image.]

[user] [Image: original 2063x1241, displayed at 2000x1203. Multiply coordinates by 1.03 to map to original image.]

[user] [Image: original 2640x160, displayed at 2000x121. Multiply coordinates by 1.32 to map to original image.]

[user] [Image: original 2280x360, displayed at 2000x316. Multiply coordinates by 1.14 to map to original image.]

[user] [Image: original 2400x330, displayed at 2000x275. Multiply coordinates by 1.20 to map to original image.]

[user] [Image: original 3240x800, displayed at 2000x494. Multiply coordinates by 1.62 to map to original image.]

[user] [Image: original 3160x640, displayed at 2000x405. Multiply coordinates by 1.58 to map to original image.]

[user] [Image: original 3370x220, displayed at 2000x131. Multiply coordinates by 1.69 to map to original image.]

[user] [Image: original 2040x900, displayed at 2000x882. Multiply coordinates by 1.02 to map to original image.]

[assistant] J'ai lu les 15 pages avec vision (plus 6 recadrages haute résolution pour lever les ambiguïtés).

```
date;vehicule;equipage;heure_depart;heure_arrivee;lieu_depart;lieu_arrivee;samu_oui_non;page_source;lisibilite
03/11/2025;Rouge;CHRIS/SOUF;2h45;3h15;URG Nimes;Dom Aymargues;montant;nov-01;partiel
04/11/2025;Rouge;CHRIS/SOUF;20h30;20h45;URG Sete;Dom;montant;nov-02;ok
04/11/2025;Rouge;CHRIS/SOUF;22h00;22h35;URG Nimes;Dom;montant;nov-02;ok
04/11/2025;Rouge;CHRIS/SOUF;22h45;23h20;Dom;URG Nimes;montant;nov-02;ok
04/11/2025;Rouge;CHRIS/SOUF;0h15;0h45;URG Lunel;UTEC;montant;nov-02;partiel
04/11/2025;Rouge;CHRIS/SOUF;1h30;1h50;URG Lap;Ephad;montant;nov-02;ok
04/11/2025;Rouge;CHRIS/SOUF;2h40;3h15;URG Beau Soleil;Dom;montant;nov-02;ok
04/11/2025;Rouge;CHRIS/SOUF;4h00;4h25;URG Lap;Dom Gigean;montant;nov-02;ok
07/11/2025;Rouge;CHRIS/SOUF;21h20;22h15;URG Beziers;ADV;montant;nov-03;ok
07/11/2025;Rouge;CHRIS/SOUF;23h45;00h40;URG Beziers;Lap;montant;nov-03;ok
07/11/2025;Rouge;CHRIS/SOUF;2h30;2h55;URG Beziers;Dom;montant;nov-03;ok
07/11/2025;Rouge;CHRIS/SOUF;3h45;4h20;URG Beziers;Dom Bessan;montant;nov-03;ok
08/11/2025;Rouge;SOUF/CHRIS (coupe);22h40;22h20;URG Bagnols;Dom;montant;nov-04;partiel
08/11/2025;Rouge;SOUF/CHRIS (coupe);23h;00h20;URG Bagnols;Lap;montant;nov-04;ok
09/11/2025;Rouge;SOUF/CHRIS;21h45;22h10;URG Beziers;Dom;montant;nov-05;ok
09/11/2025;Rouge;SOUF/CHRIS;23h;23h40;URG Beziers;Dom;montant;nov-05;ok
09/11/2025;Rouge;SOUF/CHRIS;1h15;2h;URG Beziers;Ehpad St Gervais;montant;nov-0