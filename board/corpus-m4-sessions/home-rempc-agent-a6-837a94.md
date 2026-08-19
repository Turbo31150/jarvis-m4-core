[user] Tu dépouilles des feuilles de route d'ambulance manuscrites scannées (contentieux prud'homal — ZÉRO INVENTION TOLÉRÉE).

FICHIERS : /tmp/fdr2025s1/rot/mars-01.png à /tmp/fdr2025s1/rot/mars-16.png (16 pages, déjà redressées, une page = une nuit).
Lis CHAQUE page avec l'outil Read, dans l'ordre. NE SAUTE AUCUNE PAGE. Une seule image par appel Read.
Si une page apparaît à l'envers, exécute `convert /tmp/fdr2025s1/rot/<nom>.png -rotate 180 /tmp/fdr2025s1/rot/<nom>-r180.png` puis relis.

STRUCTURE DE CHAQUE FEUILLE :
- En-tête : "Date:" (jj/mm/aa) | "Véhicules:" (ex. Violette, Rouge) | "Chauffeurs:" (ex. SOUF/JOSH)
- Tableau : Chauffeurs | Patients | Heures Départ | Heures d'Arrivée | Lieu de Départ | Lieu d'Arrivée | BS+BT OK | Numéro SAMU
- Marge gauche : petits chiffres rouges (km probables). Colonne "Numéro SAMU" : parfois un numéro, parfois des montants € rouges ajoutés après coup.
- L'équipage de nuit surveillé = "SOUF" (Soufiane DRIOUECH) et "JOSH" (Joshua BERNAD).

POINT DE VIGILANCE CAPITAL : le 3 mars 2025 l'employeur a demandé PAR ÉCRIT aux salariés de remplir leurs feuilles d'heures. Compare très attentivement les feuilles AVANT le 03/03/2025 et APRÈS : changement de soin de remplissage, apparition/disparition d'heures, nouvelles colonnes remplies, mention d'heures de prise/fin de service, changement d'écriture, densité de remplissage. Documente-le explicitement.

CE QUE TU DOIS RENVOYER — TROIS BLOCS :

BLOC 1 = lignes CSV, séparateur `;`, une ligne PAR MISSION (toute

[user] [Image: original 2125x650, displayed at 2000x612. Multiply coordinates by 1.06 to map to original image.]

[user] [Image: original 2375x450, displayed at 2000x379. Multiply coordinates by 1.19 to map to original image.]

[user] [Image: original 2100x360, displayed at 2000x343. Multiply coordinates by 1.05 to map to original image.]

[user] [Image: original 2100x600, displayed at 2000x571. Multiply coordinates by 1.05 to map to original image.]

[user] [Image: original 2500x840, displayed at 2000x672. Multiply coordinates by 1.25 to map to original image.]

[user] [Image: original 3000x500, displayed at 2000x333. Multiply coordinates by 1.50 to map to original image.]

[user] [Image: original 2450x490, displayed at 2000x400. Multiply coordinates by 1.23 to map to original image.]

[assistant] J'ai lu les 16 pages une par une, plus des agrandissements ciblés sur les zones douteuses.

---

## BLOC 1 — CSV (une ligne par mission)

```
2025-03-01;Violette;SOUF;20h15;20h40;URG Lunel;Dom GDR;montant;mars-16;ok
2025-03-01;Violette;SOUF;22h00;22h20;URG Mil;Dom Perols;montant;mars-16;ok
2025-03-01;Violette;JOSH;1h40;2h15;URG Narbonne;CH Lezignan;montant;mars-16;ok
2025-03-01;Violette;JOSH;3h50;4h50;URG Millau;URG LAP;montant;mars-16;ok
2025-03-02;Violette;Souf;20h10;21h20;Urg Saint Abrique;Utec;montant;mars-15;ok
2025-03-02;Violette;Souf;23h30;23h45;Urg st roch;Urg millenaire;montant;mars-15;ok
2025-03-02;Violette;Souf;00h30;1h10;Urg millenaire;Dom Sete;montant;mars-15;ok
2025-03-02;Violette;Josh;2h10;2h45;Urg nimes;Dom grau du roi;montant;mars-15;ok
2025-03-05;Violette;JOSH;20h30;21h30;URG Narbonne;St Elois;montant;mars-14;ok
2025-03-05;Violette;JOSH;23h00;00h00;URG Narbonne;ADV;montant;mars-14;partiel
2025-03-05;Violette;SOUF;00h50;1h20;URG Sète;Dom Marseillan;montant;mars-14;ok
2025-03-05;Violette;SOUF;2h15;2h30;URG Sète;Dom Sète;montant;mars-14;ok
2025-03-05;Violette;SOUF;3h10;3h30;URG St Jean;Dom St Georges;montant;mars-14;ok
2025-03-06;Rouge;Josh;20h30;20h40;Urg ganges;Dom ganges;montant;mars-13;ok
2025-03-06;Rouge;Josh;20h50;21h25;Urg ganges;SSA quissac;montant;mars-13;ok
2025-03-06;Rouge;Josh;23h00;23h15;Urg Lunel;Dom Lunel;montant;mars-13;ok
2025-03-06;Rouge;Josh;00h00;00h20;Urg st jean;Dom perols;montant;mars-13;ok
2025-03-06;Rouge;Souf;1h30;1h40;Urg lodeve;Ehpad