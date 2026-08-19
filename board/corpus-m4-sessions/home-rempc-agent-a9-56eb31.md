[user] Mission de LECTURE FACTUELLE de feuilles de route d'ambulance (contentieux prud'homal). RIGUEUR ABSOLUE, ZÉRO INVENTION. Tu ne dois RIEN déduire ni extrapoler : tu décris uniquement ce que tu VOIS.

Tu traites le mois de MAI 2026 : 5 pages. ATTENTION à la numérotation à UN chiffre.
- Page entière : /tmp/prime2026/r/mai-1.png ... /tmp/prime2026/r/mai-5.png
- Version haute déf : /tmp/prime2026/hi/mai-1.png ...
- Recadrage DÉJÀ PRÉPARÉ de la partie DROITE du formulaire (colonnes « BS+BT OK » et « Numéro SAMU ») : /tmp/samu/mai-1.png ... /tmp/samu/mai-5.png

MÉTHODE OBLIGATOIRE, pour CHACUNE des 5 pages :
1. Read /tmp/prime2026/r/mai-X.png (vue d'ensemble)
2. Read /tmp/samu/mai-X.png (zoom colonne SAMU) — INDISPENSABLE, ne saute jamais cette étape.
Comme tu n'as que 5 pages, sois EXTRÊMEMENT minutieux : fais en plus, pour chaque page, un recadrage ciblé de la colonne SAMU seule et lis-le, par exemple :
  convert /tmp/prime2026/hi/mai-3.png -crop 900x2151+2250+0 +repage -resize 200% /tmp/zoommai.png
(offsets en PIXELS, pas en %, sinon ImageMagick se trompe de zone) puis Read /tmp/zoommai.png. Les images hi/ font ~3100x2151.

STRUCTURE DU FORMULAIRE (gauche → droite) :
Chauffeurs | Patients | Heure de Départ | Heure d'Arrivée | Lieu de Départ | Lieu d'Arrivée | BS+BT OK | Numéro SAMU
En-tête : DATE (jj/mm/26), VÉHICULE, CHAUFFEURS (souvent « SOUF / JOSH »).
ATTENTION : les scans sont légèrement inclinés (skew). L'écriture d'une même mission peut sembler décalée d'une demi-ligne ent

[user] [Image: original 1453x2581, displayed at 1126x2000. Multiply coordinates by 1.29 to map to original image.]

[user] [Image: original 1757x3872, displayed at 908x2000. Multiply coordinates by 1.94 to map to original image.]

[user] [Image: original 1504x2581, displayed at 1165x2000. Multiply coordinates by 1.29 to map to original image.]

[user] [Image: original 1766x3872, displayed at 912x2000. Multiply coordinates by 1.94 to map to original image.]

[user] [Image: original 1534x2581, displayed at 1189x2000. Multiply coordinates by 1.29 to map to original image.]

[user] [Image: original 1791x3872, displayed at 925x2000. Multiply coordinates by 1.94 to map to original image.]

[user] [Image: original 1400x2800, displayed at 1000x2000. Multiply coordinates by 1.40 to map to original image.]

[user] [Image: original 1490x2581, displayed at 1155x2000. Multiply coordinates by 1.29 to map to original image.]

[user] [Image: original 1800x3872, displayed at 930x2000. Multiply coordinates by 1.94 to map to original image.]

[user] [Image: original 1553x2581, displayed at 1203x2000. Multiply coordinates by 1.29 to map to original image.]

[user] [Image: original 1980x3872, displayed at 1023x2000. Multiply coordinates by 1.94 to map to original image.]

[user] [Image: original 3080x1980, displayed at 2000x1286. Multiply coordinates by 1.54 to map to original image.]

[user] [Image: original 1500x2250, displayed at 1333x2000. Multiply coordinates by 1.13 to map to original image.]

[user] [Image: original 1500x2250, displayed at 1333x2000. Multiply coordinates by 1.13 to map to original image.]

[user] [Image: original 1500x2250, displayed at 1333x2000. Multiply coordinates by 1.13 to map to original image.]

[user] [Image: original 2100x1500, displayed at 2000x1429. Multiply coordinates by 1.05 to map to original image.]

[user] [Image: original 2100x1500, displayed at 2000x1429. Multiply coordinates by 1.05 to map to original image.]

[user] [Image: original 1440x4280, displayed at 673x2000. Multiply coordinates by 2.14 to map to original image.]

[assistant] J'ai lu les 5 pages (vue d'ensemble + recadrage SAMU fourni + recadrage SAMU supplémentaire que j'ai généré, plus recadrages marge gauche et colonnes horaires). Voici le relevé factuel.

## Tableau de relevé — MAI 2026 (5 pages)

| page | date (telle qu'écrite) | équipage | SOUF ? | nb missions | 1re prise en charge | dernière fin | état colonne « Numéro SAMU » | total recette en marge | remarques |
|---|---|---|---|---|---|---|---|---|---|
| mai-1 | `07/05/26` | En-tête « Chauffeurs : SOUF / JOSH ». Colonne Chauffeurs : JOSH, SOUF, SOUF, SOUF, SOUF | **OUI** (en-tête + 4 lignes sur 5) | **5** | 20h30 | 4h30 | **vide** — colonne entièrement visible (bord droit du tableau présent sur le scan), aucune inscription sur aucune ligne | **AUCUN** | Véhicule « Rouge ». Patients : COSTE, TILLIER, BOUQUET, THEPBOUAHEUANG, MOREL. Colonne « BS+BT OK » remplie « BT+BS » sur les 5 lignes. 5 petites coches bouclées en marge gauche (1 par ligne remplie) — scan en niveaux de gris, couleur indéterminable |
| mai-2 | `06/05/26` | En-tête « Chauffeurs : SOUF / JOSH ». Colonne Chauffeurs : SOUF, JOSH, JOSH | **OUI** (en-tête + 1 ligne sur 3) | **3** | 20h40 | 3h00 | **vide** — colonne entièrement visible, aucune inscription | **AUCUN** | Véhicule « Rouge ». Patients : DESAN NICOLAS, MUR, VASILEVA. « BT+BS » sur les 3 lignes. 3 coches bouclées en marge gauche (scan gris, couleur indéterminable) |
| mai-3 | `03/05/26` (le « 26 » est repassé/appuyé en noir) | En-tête « Chauffeurs : SOUF / JOSH ». Co