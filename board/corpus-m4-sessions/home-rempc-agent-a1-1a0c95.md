[user] Mission de LECTURE FACTUELLE de feuilles de route d'ambulance (contentieux prud'homal). RIGUEUR ABSOLUE, ZÉRO INVENTION. Tu ne dois RIEN déduire ni extrapoler : tu décris uniquement ce que tu VOIS.

Tu traites le mois de MARS 2026 : 15 pages.
- Page entière : /tmp/prime2026/r/mars-01.png ... /tmp/prime2026/r/mars-15.png
- Version haute déf : /tmp/prime2026/hi/mars-01.png ...
- Recadrage DÉJÀ PRÉPARÉ de la partie DROITE du formulaire (colonnes « BS+BT OK » et « Numéro SAMU ») : /tmp/samu/mars-01.png ... /tmp/samu/mars-15.png

MÉTHODE OBLIGATOIRE, pour CHACUNE des 15 pages :
1. Read /tmp/prime2026/r/mars-XX.png (vue d'ensemble)
2. Read /tmp/samu/mars-XX.png (zoom colonne SAMU) — INDISPENSABLE, ne saute jamais cette étape.
Si un détail reste douteux, refais un recadrage ciblé, par exemple :
  convert /tmp/prime2026/hi/mars-05.png -crop 1200x2151+1900+0 +repage -resize 180% /tmp/zoom.png
(offsets en PIXELS, pas en %, sinon ImageMagick se trompe de zone) puis Read /tmp/zoom.png.

STRUCTURE DU FORMULAIRE (gauche → droite) :
Chauffeurs | Patients | Heure de Départ | Heure d'Arrivée | Lieu de Départ | Lieu d'Arrivée | BS+BT OK | Numéro SAMU
En-tête : DATE (jj/mm/26), VÉHICULE, CHAUFFEURS (souvent « SOUF / JOSH »).
ATTENTION : les scans sont légèrement inclinés (skew). L'écriture d'une même mission peut sembler décalée d'une demi-ligne entre la colonne de gauche et celle de droite. Compte les missions sur la colonne « Patients » et recoupe avec « Chauffeurs » et les heures.

POUR CHAQ

[user] [Image: original 1493x2581, displayed at 1157x2000. Multiply coordinates by 1.29 to map to original image.]

[user] [Image: original 1570x2581, displayed at 1217x2000. Multiply coordinates by 1.29 to map to original image.]

[user] [Image: original 1755x3227, displayed at 1088x2000. Multiply coordinates by 1.61 to map to original image.]

[user] [Image: original 1583x2581, displayed at 1227x2000. Multiply coordinates by 1.29 to map to original image.]

[user] [Image: original 1532x2581, displayed at 1187x2000. Multiply coordinates by 1.29 to map to original image.]

[user] [Image: original 1440x3442, displayed at 837x2000. Multiply coordinates by 1.72 to map to original image.]

[user] [Image: original 1644x2581, displayed at 1274x2000. Multiply coordinates by 1.29 to map to original image.]

[user] [Image: original 2250x650, displayed at 2000x578. Multiply coordinates by 1.13 to map to original image.]

[user] [Image: original 1482x2581, displayed at 1148x2000. Multiply coordinates by 1.29 to map to original image.]

[user] [Image: original 2766x1241, displayed at 2000x897. Multiply coordinates by 1.38 to map to original image.]

[user] [Image: original 2302x2581, displayed at 1784x2000. Multiply coordinates by 1.29 to map to original image.]

[user] [Image: original 2200x840, displayed at 2000x764. Multiply coordinates by 1.10 to map to original image.]

[user] [Image: original 1505x2581, displayed at 1166x2000. Multiply coordinates by 1.29 to map to original image.]

[user] [Image: original 1572x2581, displayed at 1218x2000. Multiply coordinates by 1.29 to map to original image.]

[user] [Image: original 1568x2581, displayed at 1215x2000. Multiply coordinates by 1.29 to map to original image.]

[user] [Image: original 1543x2581, displayed at 1196x2000. Multiply coordinates by 1.29 to map to original image.]

[user] [Image: original 2250x650, displayed at 2000x578. Multiply coordinates by 1.13 to map to original image.]

[user] [Image: original 2125x625, displayed at 2000x588. Multiply coordinates by 1.06 to map to original image.]

[user] [Image: original 1534x2581, displayed at 1189x2000. Multiply coordinates by 1.29 to map to original image.]

[user] [Image: original 1481x2581, displayed at 1148x2000. Multiply coordinates by 1.29 to map to original image.]

[user] [Image: original 1531x2581, displayed at 1186x2000. Multiply coordinates by 1.29 to map to original image.]

[user] [Image: original 2578x800, displayed at 2000x621. Multiply coordinates by 1.29 to map to original image.]

[user] [Image: original 2778x660, displayed at 2000x475. Multiply coordinates by 1.39 to map to original image.]

[user] [Image: original 1400x2800, displayed at 1000x2000. Multiply coordinates by 1.40 to map to original image.]

[user] [Image: original 1514x2581, displayed at 1173x2000. Multiply coordinates by 1.29 to map to original image.]

[user] [Image: original 2250x375, displayed at 2000x333. Multiply coordinates by 1.13 to map to original image.]

[assistant] J'ai lu les 15 pages (vue d'ensemble + recadrage SAMU systématique, plus zooms ciblés sur mars-02/04/05/06/07/11/14 et sur les coins bas-droite des 15 pages).

## Tableau de relevé — MARS 2026

| page | date (telle qu'écrite) | équipage (en-tête / colonne Chauffeurs) | SOUF ? | nb missions | 1re prise en charge | dernière fin | état colonne « Numéro SAMU » | total recette en marge | remarques |
|---|---|---|---|---|---|---|---|---|---|
| mars-01 | 31/03/26 | en-tête « Souf / Josh » ; colonne : Souf ×3, Josh ×3 | **OUI** | 6 | 20h | 3h50 | **vide** (colonne entièrement visible, aucune inscription) | non | Véhicule « R ». Note surlignée vert en haut de page : « **\* BS recuperer du 16/03** ». Coches roses/fuchsia en marge gauche (1 par ligne). |
| mars-02 | 30/03/26 | en-tête « SOUF / JOSH » ; colonne : **JOSH sur les 6 lignes** | en-tête OUI / **colonne NON** ⚠️ | 6 | 20h55 | 3h30 | **TRONQUÉE : le bord droit du scan coupe la colonne** (env. 2/3 gauche visibles et vides, bord droit absent) | non | Véhicule « Rouge ». Petites coches noires en marge gauche. |
| mars-03 | 25/03/26 | en-tête « SOUF / JOSH » ; colonne : JOSH ×2, SOUF ×2 | **OUI** | 4 | 20h00 | 4h30 | **vide** (colonne entièrement visible) | non | Véhicule « Rouge ». Coches en marge gauche. |
| mars-04 | 22/03/26 | en-tête « SOUF / JOS(H) » (coupé) ; colonne : JOSH ×7, SOUF ×2 | **OUI** | 9 | 20h00 | 6h00 | **TRONQUÉE : le bord droit du scan coupe la colonne** (partie visible vide) | non | Véhicule « Rouge ». 3 miss