[user] Tu dépouilles des feuilles de route d'ambulance manuscrites scannées (contentieux prud'homal — ZÉRO INVENTION TOLÉRÉE).

FICHIERS : /tmp/fdr2025s1/rot/janv-01.png à /tmp/fdr2025s1/rot/janv-15.png (15 pages, déjà redressées, une page = une nuit).
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
- `equipage` : le contenu de la colonne "Chauffeurs" de CETTE ligne (ex. JOSH, SOUF, ou autre nom). Si vid

[user] [Image: original 2002x1281, displayed at 2000x1280. Multiply coordinates by 1.00 to map to original image.]

[user] [Image: original 2074x440, displayed at 2000x424. Multiply coordinates by 1.04 to map to original image.]