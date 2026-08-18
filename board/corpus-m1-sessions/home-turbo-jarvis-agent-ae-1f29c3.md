[assistant] Environnement sondé. `statsmodels`, R, `brms`/`lme4`, `pymc` sont **absents** ; seuls numpy 2.5.1 / scipy 1.18.0 / pandas 3.0.5 / sklearn sont présents. Je calcule maintenant les seuils de puissance réels avant de rédiger.

[assistant] Chiffres obtenus. Point critique : avec N=5, le Wilcoxon apparié **ne peut structurellement pas** descendre sous p=0,0625. J'écris maintenant le code d'analyse et je le smoke-teste avant de le mettre dans le livrable.

[assistant] Deux défauts réels : la série synthétique est trop courte pour la bande passante (aucun placebo possible), et la dimension `autocorr` du multivers ne change effectivement rien. Je corrige les deux.

[assistant] Maintenant les returns précoces de `placebo_in_time`, la dimension `autocorr`, et la longueur de la série synthétique.

[assistant] Le smoke test tourne en fond (bloc-bootstrap sur 400 spécifications = long). Je rédige le livrable pendant ce temps.

[assistant] Pendant l'attente, je valide les fonctions clés isolément avec des paramètres légers.

[assistant] Le code fonctionne et livre un enseignement que je dois rapporter : sur une réalisation AR(1) fortement autocorrélée, l'estimateur retenu surestime l'effet connu (5,81 pour un vrai +4,0). J'ajoute ces mesures réelles au livrable.

[assistant] Le multivers brut révèle un défaut réel de ma conception : il agrège des τ exprimés en °C, en log-°C et en rangs — l'IQR [0,06 ; 367] est ininterprétable. Je corrige le code et le document.

[assistant] La lecture stratifiée est cohérente (médiane 3,49 °C en unités brutes pour un vrai +4,0) et l'artefact d'échelle disparaît. J'intègre ces résultats et la règle qu'ils imposent.

[assistant] Je mets à jour l'extrait de code dans le document pour refléter les corrections apportées au fichier exécutable.

[assistant] L'auto-test dépasse 15 min — inacceptable pour un auto-test. La cause est `n_effectif()` recalculé dans chaque ajustement des boucles bootstrap. Je le rends optionnel.

[assistant] Le processus est arrêté. J'optimise `rdit_fit` pour rendre l'auto-test praticable.

[assistant] Résultat décisif : avec un effet vrai **identique** (+4,00) sur les cinq cartes, les estimations s'étalent de **+2,75 à +5,81 °C**. J'intègre ce garde-fou d'interprétation.

[assistant] Je synchronise maintenant les chiffres de la §5.4 avec le run reproductible de l'auto-test.

[assistant] Livrable terminé et vérifié par exécution.

**Méthode retenue — T ≈ 0,25** : RDiT (régression sur discontinuité temporelle) locale, **estimée par unité sans jamais agréger**, avec inférence par randomisation *placebo-in-time*, IC par bloc-bootstrap stationnaire (Politis–Romano), Romano–Wolf pour les 20 tests, et restitution en courbe de spécification. Directions écartées : A (modèle mixte, T ≈ 0,70) et B (ITS bayésienne, T ≈ 0,45) — toutes deux structurées autour d'un effet aléatoire « carte », donc autour de l'échangeabilité qui est précisément fausse ici, et toutes deux **infaisables localement** (R, `brms`, `lme4`, `statsmodels`, `pymc` absents ; rien installé).

**Deux raisons majeures du rejet des méthodes modales** : (1) les unités ne sont pas échangeables — il n'existe pas de population de GPU dont ces 5 cartes seraient un tirage, donc « l'effet moyen sur une carte typique » n'a aucun estimande entre une 1660S 70 W et une 3080 230 W ; (2) l'autocorrélation détruit les erreurs-types — mesuré : ACF(1) = 0,948, N effectif = 57 pour 601 mesures, erreur-type naïve **2,02× trop petite**. S'y ajoute une erreur d'unité d'analyse : le débit a N = 1 (le service), pas N = 5.

**Taille d'effet minimale détectable avec N = 5** : **d = 1,682** (t apparié, α = 0,05 bilatéral, puissance 0,80), soit ≈ 5 °C ou ≈ 6,7 tok/s. Un effet « grand » (d = 0,80) n'est détecté que 28 % du temps. Et le Wilcoxon souvent recommandé pour petit N a un **plancher de p à 0,0625 > 0,05** : il ne peut stru

[assistant] Cette assignation correspond à la tâche que je viens d'achever. Je vérifie que les livrables sont intacts plutôt que de refaire le travail.

[assistant] Les livrables sont intacts et complets — la tâche #8 était déjà terminée avant cette assignation.

**État : livré.** `/home/turbo/jarvis/artifacts/e1-20260806/volet3-cadre-methodologique.md` (1 041 lignes, 8 sections : Phases 0-5 + Code ex-E4 + Sensibilité ex-E5) et `/home/turbo/jarvis/artifacts/e1-20260806/rdit_analysis.py` (718 lignes, syntaxe validée, auto-test en 13 s).

Rappel des conclusions, inchangées :

**Méthode retenue, T ≈ 0,25** — RDiT locale à estimation par unité non agrégée + inférence par randomisation *placebo-in-time* + bloc-bootstrap stationnaire + Romano–Wolf + courbe de spécification. Directions A (mixte, T ≈ 0,70) et B (ITS bayésienne, T ≈ 0,45) écartées : elles reposent toutes deux sur l'échangeabilité des cartes, fausse ici, et sont **infaisables localement** (R, `brms`, `lme4`, `statsmodels`, `pymc` absents ; rien installé).

**Deux motifs de rejet des méthodes modales** : unités non échangeables (aucun estimande pour « l'effet moyen » entre une 1660S 70 W et une 3080 230 W) ; autocorrélation qui détruit les erreurs-types (ACF(1) = 0,948 ; N effectif 57 pour 601 ; erreur-type naïve 2,02× trop petite).

**Effet minimal détectable avec N = 5** : d = 1,682 (≈ 5 °C / ≈ 6,7 tok/s). Le Wilcoxon plafonne à p = 0,0625 — il ne peut jamais conclure.

**Multivers** : 15 552 spécifications.

**Confiance globale : 57/100**, abaissé depuis 62 par l'exécution du code, qui a révélé deux défauts non anticipés (biais de +45 % de la RDiT sur une réalisation AR(1) ; imp