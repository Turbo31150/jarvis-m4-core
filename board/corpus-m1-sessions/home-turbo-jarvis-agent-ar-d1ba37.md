[assistant] Le `chemin` est vide dans le catalogue, et la casse du `repo` diffère. J'écris le script avec dérivation du slug depuis le chemin du corpus.

[assistant] Recouvrement à 10,6 % seulement : ma dérivation de slug rate 43 % des cas alors que le dépôt est présent. Je construis un cache d'index pour diagnostiquer sans relire 5,2 Go.

[assistant] Le corpus ne couvre que 1 304 dépôts au total. Je teste une clé plus fiable : la description du frontmatter.

[assistant] La clé « nom du dossier » débloque 30 % de plus. Je teste le départage des ambiguïtés par la description du frontmatter.

[assistant] Le vrai identifiant est la **queue de l'URL**, pas la colonne `slug` (tronquée). Je refais la mesure.