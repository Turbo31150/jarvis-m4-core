[assistant] Base lue en RO, schéma connu. Je cartographie maintenant l'arborescence par strate.

[assistant] Découverte majeure : le volume n'est pas 688 749 fichiers, c'est un JSONL unique. Je vérifie.

[assistant] Le gisement réel : 106 fichiers, dont un JSONL de 5,4 Go (1 ligne = 1 fichier source). J'échantillonne avant tout balayage.

[assistant] L'index TSV me donne un accès aléatoire par offset — je peux échantillonner sans lire les 5,4 Go. Analyse de l'index complet d'abord.

[assistant] Stock homogène : 100 % de `.md`, dont 677 565 `SKILL.md` — mais seulement 1 304 repos. Je mesure la concentration.

[assistant] Concentration extrême : 5 repos = 63 % du stock, dont un miroir de registre à 202 485 fichiers. Je chronomètre un pilote avant le balayage complet.

[assistant] Trop lent avec 37 regex séparées. Je fusionne en une regex unique et relance en arrière-plan.

[assistant] Load à 18,6 — sous le seuil. Pendant le balayage, j'examine le filtre en amont du pipeline.

[assistant] Le cap anti-miroir (2000/repo) existe déjà dans le code — mais un repo à 202 483 lignes est présent. Je vérifie s'il a été appliqué.

[assistant] Le cap fonctionne dans le flux actuel (9 repos cappés) — le stock à 202k lignes est antérieur. Je quantifie les deux régimes.

[assistant] Load à 23,7 — au seuil. Je dépriorise le balayage plutôt que de perdre le travail déjà fait.

[assistant] Le balayage tourne (6 workers à 92 %, priorité abaissée). En attendant, je lis les axes de classement déjà présents en base.

[assistant] Sections 1 et 2 sont chiffrées. J'écris le rapport pendant que le balayage termine.

[assistant] Load redescendu à 18,4. Je prépare le script d'extraction qualitative des candidats, prêt à s'exécuter dès la fin du balayage.

[assistant] Je chaîne l'extraction qualitative pour qu'elle s'exécute dès la fin du balayage.

[assistant] Analyse complémentaire légère : distribution des tailles, déduite des offsets de l'index.

[assistant] Vérification utile pour la recommandation : recoupement avec les skills déjà installés localement.

[assistant] Recoupement entre les noms du gisement et les 573 skills locaux — extractible de l'index sans relire le JSONL.

[assistant] Échantillon qualitatif aléatoire par seek direct — 6 fiches tirées uniformément.

[assistant] Contenu réel et substantiel (médiane 5,5 Ko). Je note un marqueur de dégradation : double frontmatter empilé dans les fiches ré-empaquetées par les registres. J'attends la fin du balayage pour les sections 3 à 5.

[assistant] Je lance une mesure croisée indépendante des doublons via le `sha` git (hash du blob), bien plus rapide que le balayage de contenu.

[assistant] La mesure croisée révèle un fait : seules 349 108 lignes (51 %) ont un `sha` non vide — les autres viennent de dépôts dont l'arbre git a été tronqué par l'API. Je vérifie l'état du balayage principal.

[assistant] J'intègre les mesures déjà consolidées dans le rapport pendant que le balayage finit.

[assistant] La mesure d'offset est bloquée par les permissions `/proc`. Je relance une attente avec chaînage, le background précédent risquant d'expirer.

[assistant] Le journal est passé de 9 à 10 caps pendant l'analyse — cible mouvante confirmée. Je corrige.

[assistant] Filet de sécurité pour la section 3 : pré-filtrage par domaine sur les dépôts non-miroirs, indépendant du balayage.

[assistant] J'intègre ce pré-filtrage comme section 3 partielle, en attendant l'analyse de contenu.

[assistant] C'était l'ancien Monitor qui expirait ; le second reste armé. Je vérifie l'état.

[assistant] La charge est retombée à 11,4 — je rends leur priorité normale aux workers pour accélérer la fin.

[assistant] Je calcule le gain exact de la purge en octets, à partir des tailles réelles déduites des offsets.

[assistant] Je consolide l'affirmation clé sur les `sha` vides par un comptage direct borné.

[assistant] 382 523 lignes à `sha` vide sur la borne figée. Le balayage me donnera le dénominateur exact.

[assistant] Le balayage approche des 21 minutes. J'attends sa fin — le Monitor est armé jusqu'à 14:46 et me livrera les résultats de la section 3.

[assistant] Le livrable demande une méthode d'échantillonnage explicite. J'ajoute cette section.

[assistant] Le classement brut est biaisé vers les méga-fichiers et dominé par les dépôts-miroirs. Je re-classe hors miroirs, dédupliqué, avec extraction propre des noms.

[assistant] Je lis le contenu réel des meilleurs candidats pour juger sur pièces, pas sur métadonnées.

[assistant] Rapport complet et vérifié : aucune écriture dans la cible.

**`/home/turbo/jarvis/artifacts/e1-20260806/moisson-source-github.md`** (729 lignes)

**Volumétrie — la prémisse était fausse.** Le répertoire contient **106 fichiers**, pas 688 749 : le gisement est **un seul JSONL** de 5,4 Go (96,3 % du volume), 1 ligne = 1 fichier source. Les 683 033 « fichiers » sont des lignes, indexées par offset dans `sources-index.tsv` — d'où un accès aléatoire par `seek` sans relire les 5,4 Go.

**Types : 100 % du Markdown.** 675 290 `SKILL.md`, 3 450 `AGENTS.md`, 2 275 `skill.md`, 2 018 `AGENT.md`. Zéro JSON, zéro HTML, zéro script — conforme à `github_source.py:27`. Conséquence : **aucun skill n'est installable**, les `scripts/` référencés ne sont jamais aspirés. `avale/` (brut du site) et `export/` (dérivés) ne contiennent pas la même chose.

**Écart d'ingestion — il va dans l'autre sens.** 0 dépôt sur disque absent de la base ; le disque est un sous-ensemble strict. Le vrai retard : **5 000 dépôts catalogués sans source** et 3 004 encore en file. Le ratio 33,4× (677 565 `SKILL.md` pour 20 305 fiches) est **structurel**, pas un retard : `claude-skill-registry` publie 89 skills et contient 202 483 `SKILL.md`.

**Applicables : 31 783** passent les 5 critères (≥2 outils installés + domaine + bloc bash + ≥800 o + dédup md5) ; **58** subsistent après exclusion des miroirs et dédup. Les 5 meilleurs, jugés sur contenu relu :
1. `lev-os/agents :: system-performance-remediation` — limites mémoire