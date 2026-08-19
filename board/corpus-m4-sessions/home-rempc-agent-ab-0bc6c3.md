[user] Mission de VÉRIFICATION et de comptage pour un contentieux prud'homal. RIGUEUR ABSOLUE, ZÉRO INVENTION.

CONTEXTE : sur les feuilles de route (FDR) de SOLEIL AMBULANCES, la colonne pré-imprimée « Numéro SAMU » a été détournée sur certaines périodes pour y porter des MONTANTS DE FACTURATION EN EUROS ajoutés après coup (encre rouge/rose). On affirme que sur MARS, AVRIL, MAI et JUILLET 2026 cette colonne est ENTIÈREMENT VIDE. Tu dois VÉRIFIER cette affirmation page par page, et compter l'activité.

IMAGES DÉJÀ PRÊTES, déjà redressées (rotation -90) et contrastées :
- /tmp/prime2026/r/mars-01.png ... mars-15.png (15 pages)
- /tmp/prime2026/r/avril-01.png ... avril-14.png (14 pages)
- /tmp/prime2026/r/mai-1.png ... mai-5.png (5 pages, attention : numérotation à UN chiffre)
- /tmp/prime2026/r/juillet-01.png ... juillet-11.png (11 pages)
Versions haute déf disponibles dans /tmp/prime2026/hi/ (mêmes noms). Si besoin, recadre :
  convert /tmp/prime2026/hi/avril-05.png -crop 40%x100%+60%+0 +repage -resize 200% /tmp/cropv.png
puis Read /tmp/cropv.png.

Total : 45 pages. Lis CHAQUE page avec Read.

STRUCTURE DU FORMULAIRE (colonnes de gauche à droite) :
Chauffeurs | Patients | Heure de Départ | Heure d'Arrivée | Lieu de Départ | Lieu d'Arrivée | BS+BT OK | Numéro SAMU
En haut : DATE (jj/mm/26), VÉHICULE, CHAUFFEURS (souvent « SOUF / JOSH »).

POUR CHAQUE PAGE, relève UNIQUEMENT :
1. Numéro de page
2. DATE de la feuille
3. ÉQUIPAGE, et si SOUF (Soufiane) y figure — signale très clairement

[user] [Image: original 1398x2259, displayed at 1238x2000. Multiply coordinates by 1.13 to map to original image.]

[user] [Image: original 1433x2581, displayed at 1110x2000. Multiply coordinates by 1.29 to map to original image.]

[assistant] The crop pipeline works. Now launching parallel per-month readers while I verify flagged pages myself.

[assistant] While the month readers run, let me independently check the control months (janv/fev) where red ink WAS detected in the right band — to validate what a "montant in the SAMU column" actually looks like.

[user] [Image: original 1489x2581, displayed at 1154x2000. Multiply coordinates by 1.29 to map to original image.]

[assistant] Positive control confirmed: on janv-03 the SAMU column is filled with red-ink amounts (112,83 / 93,05 / 239,49 …) plus a total "1440". Now let me make the ink detection geometry-aware rather than using fixed percentage bands.

[assistant] The blob metric is confounded by grid lines — discarding it. The red-ink metric is the validated one. Let me verify the second control (fev-14) and check the two pages whose table edge sits at the image border (possible truncation).

[user] [Image: original 1540x2366, displayed at 1302x2000. Multiply coordinates by 1.18 to map to original image.]

[user] [Image: original 1456x2179, displayed at 1336x2000. Multiply coordinates by 1.09 to map to original image.]

[user] [Image: original 2600x1240, displayed at 2000x954. Multiply coordinates by 1.30 to map to original image.]

[assistant] Controls validated (janv-03 and fev-14 both show €-amounts in the SAMU column with a total). Verified myself: mars-05 SAMU column empty and not truncated; mars-14 SAMU column contains a phone-number annotation. Waiting on the month readers.

[assistant] All four readers are back. Two claims contradict my geometric measurements — let me verify them personally before concluding.

[user] [Image: original 2044x2173, displayed at 1881x2000. Multiply coordinates by 1.09 to map to original image.]

[user] [Image: original 2210x1530, displayed at 2000x1385. Multiply coordinates by 1.10 to map to original image.]

[assistant] Two final verifications: mars-02/mars-04 truncation is confirmed (my geometric metric was wrong, the readers were right), and avril-07's "4400339" is confirmed as a 7-digit number in black, not a euro amount. Last check: mars-07, reported as cut at the bottom.

[user] [Image: original 2766x1241, displayed at 2000x897. Multiply coordinates by 1.38 to map to original image.]

[assistant] All 45 pages read (each: full page + dedicated crop of the SAMU column), plus my own independent checks on the disputed pages and on two control sheets outside the period.

---

# (A) RELEVÉ PAGE PAR PAGE

## MARS 2026 — 15 feuilles (véhicule R / Rouge)

| page | date | équipage (en-tête / colonne) | SOUF ? | missions | 1re p.e.c. | dernière fin | amplitude plancher | colonne « Numéro SAMU » | total recette marge | remarques |
|---|---|---|---|---|---|---|---|---|---|---|
| 01 | 31/03/26 | Souf/Josh ; Souf×3, Josh×3 | OUI | 6 | 20h00 | 3h50 | 7h50 | **vide** | non | Note surlignée vert : « ✱ BS recuperer du 16/03 » ; coches roses en marge G |
| 02 | 30/03/26 | SOUF/JOSH ; **JOSH ×6** | en-tête oui / **colonne NON** ⚠ | 6 | 20h55 | 3h30 | 6h35 | **TRONQUÉE** au bord droit — partie visible vide | non | Conclusion impossible sur la part manquante |
| 03 | 25/03/26 | SOUF/JOSH ; JOSH×2, SOUF×2 | OUI | 4 | 20h00 | 4h30 | 8h30 | **vide** | non | |
| 04 | 22/03/26 | SOUF/JOS(H) ; JOSH×7, SOUF×2 | OUI | 9 | 20h00 | 6h00 | 10h00 | **TRONQUÉE** au bord droit — partie visible vide | non | 3 missions consécutives même patient (LOMBARTE) |
| 05 | 21/03/26 (?) | Josh/Souf ; Josh×1, Souf×11 | OUI | 12 | 20h00 | 6h30 | 10h30 | **vide** (vérifié par moi) | non | Journée la plus chargée du mois |
| 06 | 20/03/26 | Souf/Josh ; Josh×3(?), Souf×1 | OUI | 4 | 20h00 | 4h00 | 8h00 | **vide** | non | Colonne Chauffeurs très pâle |
| 07 | 17/03/26 | Josh/So(u)f (?) ; Josh×2, 1 case vide | en-tête prob