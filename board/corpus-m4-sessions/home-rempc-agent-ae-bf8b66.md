[user] Mission d'extraction de données pour un contentieux prud'homal. RIGUEUR ABSOLUE, ZÉRO INVENTION.

Tu dépouilles les feuilles de route (FDR) de JANVIER 2026 de la société SOLEIL AMBULANCES.

IMAGES DÉJÀ PRÊTES, déjà redressées (rotation -90 appliquée) et contrastées :
- Basse déf (1824x1241 environ) : /tmp/prime2026/r/janv-01.png ... /tmp/prime2026/r/janv-15.png (15 pages)
- Haute déf (260 dpi) : /tmp/prime2026/hi/janv-01.png ... janv-15.png

Lis CHAQUE page avec l'outil Read. Commence par la version /tmp/prime2026/r/. Si un montant ou une heure est difficile à lire, RECADRE la zone avec ImageMagick sur la version haute déf, par exemple :
  convert /tmp/prime2026/hi/janv-05.png -crop 40%x100%+60%+0 +repage -resize 200% /tmp/crop.png
puis Read /tmp/crop.png. Tu peux recadrer autant de fois que nécessaire.

STRUCTURE DU FORMULAIRE (colonnes de gauche à droite) :
Chauffeurs | Patients | Heure de Départ | Heure d'Arrivée | Lieu de Départ | Lieu d'Arrivée | BS+BT OK | Numéro SAMU
En haut de page : la DATE (format jj/mm/26), le VÉHICULE, et les CHAUFFEURS (souvent « SOUF / JOSH », parfois d'autres noms comme « Christ », « Chris »...).

POINT CRUCIAL : la colonne « Numéro SAMU » a été DÉTOURNÉE pour y porter des MONTANTS DE FACTURATION EN EUROS, ajoutés après coup (encre différente, rouge/rose ou crayon). Exemples déjà relevés page janv-15 : 93,05 — 102,36 — 169,4? — avec un total en marge de type « 950 ». Ce sont des EUROS AVEC DÉCIMALES (virgule), PAS des centimes.

⚠️ ATTENTION : 

[user] [Image: original 4529x710, displayed at 2000x314. Multiply coordinates by 2.26 to map to original image.]

[user] [Image: original 2990x1657, displayed at 2000x1108. Multiply coordinates by 1.50 to map to original image.]

[user] [Image: original 2115x755, displayed at 2000x714. Multiply coordinates by 1.06 to map to original image.]

[user] [Image: original 2115x645, displayed at 2000x610. Multiply coordinates by 1.06 to map to original image.]

[user] [Image: original 2299x812, displayed at 2000x706. Multiply coordinates by 1.15 to map to original image.]

[assistant] J'ai dépouillé les 15 pages. J'ai travaillé sur `/tmp/prime2026/r/` + recadrages haute déf, et j'ai en plus ré-extrait les images **couleur natives du PDF source** (`/home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/feuille de route/2026/FDR janv 2026.pdf`, 15 pages, ~340 ppi) vers `/tmp/prime2026/col/` — meilleure lecture, et c'est là qu'on voit que sur janv-03 les montants sont bien **à l'encre rouge/rose**, ajoutés après coup.

---

## (A) Tableau page par page

| page | date | véh. | équipage | SOUF ? | nb missions | 1re PEC | dernière fin | amplitude plancher | montants € portés en colonne « Numéro SAMU » | total marge | illisibles | remarques |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| janv-01 | 05/01/26 (mois surchargé) | R | Chris / Souf | **oui** | 5 | 20:00 | 04:00 | 8h00 | 144,32 · **37?,15** · **1?4,36** · 112,33 · 112,33 | **850** | 2 | 2 montants raturés/écrasés par le filet du tableau |
| janv-02 | 06/01/26 | R | Chris / Souf | **oui** | 4 | 20:00 | 03:35 | 7h35 | 125,14 · 169,47 · 276,22 · 152,86 | **725** | 0 | montants écrits **en débord à droite** de la colonne, à la limite du bord scanné — lisibles mais de justesse |
| janv-03 | 09/01/26 | R | Chris / Souf | **oui** | 12 (dont 1 ligne sans heures) | 20:00 | 05:00 | 9h00 | 112,33 · 93,05 · 93,05 · 115,83 · 239,49 · 106,63 · 106,63 · 120,87 · 102,36 · 102,36 · 116,60 · 130,06 | **1440** | 0 | seule page en couleur : **montants à l'encre rouge**, corps de feuille au stylo bleu → détournement de colon