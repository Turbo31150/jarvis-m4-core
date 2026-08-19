[user] Tu dépouilles des feuilles de route d'ambulance manuscrites scannées (contentieux prud'homal — ZÉRO INVENTION TOLÉRÉE).

FICHIERS : /tmp/fdr2025s1/rot/juin-01.png à /tmp/fdr2025s1/rot/juin-14.png (14 pages, déjà redressées, une page = une nuit).
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

[user] [Image: original 2250x175, displayed at 2000x156. Multiply coordinates by 1.13 to map to original image.]

[user] [Image: original 2800x300, displayed at 2000x214. Multiply coordinates by 1.40 to map to original image.]

[assistant] J'ai lu les 14 pages (avec zooms de contrôle sur les cellules ambiguës : dates, heures, ratures, annotations).

**Avertissement de lecture** : le scripteur trace le « 1 » avec un fanion (⌐1) qui ressemble à un « 4 ». Vérification par zoom sur juin-01, 04, 05, 12 → les heures et la date de juin-05 sont corrigées en conséquence (juin-05 = **21/06/25**, pas 24/06). L'ordre des 14 pages est strictement décroissant en date, ce qui confirme cette lecture.

---

## BLOC 1 — CSV (une ligne par mission)

```
2025-06-30;Violette;SOUF;20h30;20h55;URG Parc;Dom St Clément;montant;juin-01;ok
2025-06-30;Violette;SOUF;22h00;22h20;URG St Jean;Dom Mtp.;montant;juin-01;partiel
2025-06-30;Violette;SOUF;23h15;23h45;URG Lunel;Dom St Laurent;montant;juin-01;ok
2025-06-30;Violette;SOUF;1h15;1h45;URG Parc;Stella;montant;juin-01;ok
2025-06-30;Violette;SOUF;2h20;2h40;UTEC;Dom Fabrègues;montant;juin-01;ok
2025-06-30;Violette;SOUF;3h10;3h35;URG LAP;Dom Lunel;montant;juin-01;partiel
2025-06-26;Violette;JOSH;1h00;1h15;URG Béziers;UHAS Béziers;montant;juin-02;partiel
2025-06-26;Violette;SOUF;1h40;3h00;URG Béziers;Dom Salvetat;montant;juin-02;partiel
2025-06-25;Rouge;Josh;20h30;20h50;Urg parc;Dom Palavas;montant;juin-03;ok
2025-06-25;Rouge;Josh;22h45;23h20;Urg ganges;CL du cros quissac;montant;juin-03;partiel
2025-06-25;Rouge;JOSH;00h30;00h55;URG Sète;Dom Marseillan;montant;juin-03;ok
2025-06-25;Rouge;JOSH;1h30;2h00;URG Sète;Dom Agde;montant;juin-03;ok
2025-06-25;Rouge;SOUF;3h00;3h20;URG St Privat;?;montant;