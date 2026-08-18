[assistant] Charge à 6,74 sur 16 cœurs — marge confortable. J'inspecte l'état actuel de la base.

[assistant] Baseline confirmée : 1 795 clés distinctes, `m1-reel` à 0,5831. Je mesure le volume de travail avant de modifier quoi que ce soit.

[assistant] 3 M de commandes au total (11,3/logique). Je modifie le sélecteur de vague : deux changements ciblés.

[assistant] 4 000 logiques en 2 s — le cache `which` a levé le goulot. Deux points avant de lancer large : la place disque, et un réessai sur verrou.

[assistant] Fichier sain. Je lance la première extension : 40 000 logiques (la cible), en avant-plan puisque c'est court.

[assistant] 42 195 logiques en 18 s, charge stable à 9,8. Puisque c'est si peu coûteux, je couvre le corpus **entier** — cela supprime d'un coup la question de la représentativité de l'échantillon.

[assistant] Séparation nette : l'échantillon d'origine est le lot de 05:13. Analyse comparative complète.

[assistant] Le classement des manquants révèle un défaut : `Export`, `Python`, `const`, `data` ne sont pas des binaires. Je quantifie.

[assistant] Mission terminée : corpus **intégralement** couvert. Charge finale 8,55 (plafond 24), rien commité, seule `simulation_logique` écrite.

## 1. Couverture

| | avant | après |
|---|---|---|
| logiques distinctes | 1 795 (0,7 %) | **268 898 (100 %)** |
| profils | 3 | 3 (`m1-reel`, `poste-dev`, `socle-nu`) |
| lignes en base | 5 400 | 806 709 |

Durée totale ≈ 2 min. Ayant vu que 4 000 logiques prenaient 2 s, je suis allé au-delà des 40 000 demandés jusqu'au corpus entier — cela supprime la question de la représentativité au lieu de la déplacer.

## 2. Le chiffre publié était honnête

| profil | échantillon 1 800 | corpus 268 898 | écart |
|---|---|---|---|
| **m1-reel** | **0,583** · 34,4 % à 100 % | **0,589** · 34,2 % à 100 % | **+0,006** |
| poste-dev | 0,468 · 24,4 % | 0,487 · 25,4 % | +0,019 |
| socle-nu | 0,203 · 7,5 % | 0,204 · 7,5 % | +0,001 |

+1,0 % en relatif sur `m1-reel`, et le taux de recettes 100 % jouables bouge de −0,2 point. Le tirage uniforme sur 1 800 était représentatif : présenté comme valant pour le corpus, il le valait effectivement. Le reproche à faire portait sur l'absence de preuve, pas sur le chiffre.

## 3. Par famille d'outil (`m1-reel`) — une logique peut relever de plusieurs familles

| famille | logiques | score | 100 % jouables |
|---|---|---|---|
| python | 75 559 | 0,727 | 40,7 % |
| git | 30 187 | 0,718 | 29,2 % |
| système | 57 301 | 0,691 | 29,3 % |
| curl/web | 40 360 | 0,661 | 29,4 % |
| bases de données | 1 636 | 0,643 | 16,7 % |
| npm/n