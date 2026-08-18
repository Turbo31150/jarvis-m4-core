[user] INVESTIGATION EN LECTURE SEULE. Ne modifie/supprime/tronque AUCUN fichier — `~/labo/bibliotheque/skillsmp/sources.jsonl` est écrit en direct par un process actif (`github_source.py`). Lis-le sans le verrouiller (pas de réécriture, pas de tri en place). Tu produis un rapport, rien d'autre.

CONTEXTE : `sources.jsonl` fait ~5,2 Go. Une ligne = un fichier collecté depuis GitHub, JSON avec champs `repo`, `branche`, `chemin`, `sha`, `taille`, `contenu`. L'injecteur `~/labo/bibliotheque/skillsmp/injecte.py` le RELIT INTÉGRALEMENT à chaque cycle du superviseur (~toutes les 10 min) — donc sa taille pèse sur tout le pipeline.

TÂCHE (échantillonne, ne charge jamais les 5,2 Go en mémoire d'un coup — utilise `head`, `wc -l`, lecture ligne à ligne en streaming Python) :
1. Nombre total de lignes. Taille moyenne d'une ligne.
2. Doublons : combien de lignes partagent le même `(repo, chemin)` ? (l'étage source a été relancé plusieurs fois et fait `append` — suspicion de ré-écriture des mêmes fichiers à chaque relance). Estime le % de lignes redondantes en streaming (dict de hash sur repo+chemin, compte les répétitions ; si trop volumineux, échantillonne 500 000 lignes).
3. Quels `repo` pèsent le plus (top 10 par nombre de lignes) — les dépôts riches (tri par richesse) dominent-ils ?
4. Y a-t-il des `contenu` énormes (>200 Ko) qui n'auraient pas dû passer le garde-fou TAILLE_MAX ?

SORTIE ATTENDUE (concise) : lignes totales, % de doublons (repo,chemin) estimé, top 10 repos par volume, verdic

[assistant] Je vais commencer par des mesures de base sans jamais charger le fichier entier en mémoire.

[assistant] Le fichier fait 5,29 Gio (5 542 987 429 octets). Une ligne = un fichier GitHub avec `contenu` inline. Je lance une passe unique en streaming (mémoire bornée) pour tout mesurer d'un coup.

[assistant] Pendant que la passe complète tourne, je regarde en parallèle l'injecteur et le producteur pour cadrer l'impact et le garde-fou TAILLE_MAX.

[assistant] Le code confirme déjà deux points clés: `TAILLE_MAX = 200_000` octets (garde-fou dans la branche tarball, `membre.size > TAILLE_MAX` sauté) et l'écriture en `open(OUT, "a")` (append — d'où l'accumulation à chaque relance). Je lis la fin de `injecte.py` pour voir comment il relit `sources.jsonl` et s'il déduplique.

[assistant] Résultats clairs. Un point mérite vérification: les gros repos "registry" sont des miroirs qui recopient les mêmes fichiers skill — la dédup `(repo,chemin)` ne capte pas cette redondance inter-repos, mais le champ `sha` oui. Je fais une 2e passe rapide sur `sha` (redondance de contenu réelle), et je vérifie l'état du producteur.

[assistant] La 2e passe change le diagnostic: 65% du fichier est du contenu identique (même `sha`) recopié entre repos miroirs. Je vérifie proprement l'état du producteur (le pgrep précédent a matché ma propre commande).

[assistant] Investigation terminée. Producteur `github_source.py` non actif en ce moment (mtime 02:04, `lsof` vide, collecteur source hors cycle) — le fichier n'a jamais été verrouillé, aucune écriture pendant l'analyse.

---

# Rapport — `~/labo/bibliotheque/skillsmp/sources.jsonl`

Analyse par 2 passes streaming (jamais de chargement intégral), plus lecture de `github_source.py` et `injecte.py`.

## 1. Volumétrie
| Mesure | Valeur |
|---|---|
| Taille | 5 542 987 429 o = **5,29 Gio** |
| Lignes totales | **683 033** |
| Octets moyens / ligne | **8 115 o** |
| Ligne max | 206 422 o |
| JSON invalides | 0 |

## 2. Doublons `(repo, chemin)` — l'hypothèse est FAUSSE
- **6 853 lignes redondantes = 1,0 %** (≈ 55 Mo). 676 180 paires uniques.
- L'`append` à chaque relance ne recopie **pas** les fichiers : le marqueur `repos-faits.txt` (lu au démarrage de `github_source.py`) gate correctement les repos déjà collectés. Dédupliquer sur `(repo,chemin)` ne gagnerait que ~1 %. **Inutile.**

## 3. La vraie graisse : contenu identique inter-repos (`sha`)
- **445 704 lignes = 65,25 % ont un `sha` déjà vu** → **3,59 Go redondants**. Seulement **237 329 `sha` uniques**.
- Cause : les gros dépôts « registry / marketplace » sont des **miroirs** qui recopient les mêmes fichiers skill. La dédup `(repo,chemin)` ne le voit pas (le `repo` diffère), mais le `sha` oui.

## 4. Top repos par volume — oui, les repos riches écrasent tout
| Lignes | % | Repo |
|---|---|---|
| 202 485 | 29,6 % | majiayu000/claude-skill