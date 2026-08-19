# findings.md — mesures de la session du 18-19/08/2026

Toute valeur ici est **mesurée**, jamais estimée. Chaque ligne porte sa date.

---

## Infrastructure

| Fait | Mesure | Date |
|---|---|---|
| CDP `:9222` | mort — et `chrome-devtools-mcp` (PID 58225) pointe dessus, donc inopérant | 19/08 |
| CDP `:9100` | vivant — BrowserOS Chrome/148, profil persistant `~/.config/browser-os` | 19/08 |
| CDP `:9108` | vivant — browserless Chrome/151, profil éphémère, 0 onglet | 19/08 |
| BrowserOS server | `--cdp-port=9100 --server-port=9200 --extension-port=9300` | 19/08 |
| M6 `10.42.0.230:1234` | sert `qwen/qwen3.5-9b` **et** `text-embedding-nomic-embed-text-v1.5` (768 d) | 19/08 |
| Délocalisation du compute | 141 générations : M4 à 2,0 % CPU / 27 °C, RTX 3080 de M6 à 69 % / 75 °C | 19/08 |
| `nvidia-smi` sur M4 | fonctionne (RTX 3050, driver 595.84) — le garde-fou 84 °C protège à nouveau | 19/08 |
| n8n | 65 workflows actifs, dont 2 LinkedIn | 19/08 |
| Table ronde | 11 moteurs/sièges joignables sur 13 | 19/08 |
| board.db | 260 200 chunks | 19/08 |

## Accessibilité des sources (sondée, pas supposée)

| Source | HTTP | Retenue |
|---|---|---|
| Google Trends RSS FR | 200 | non — divertissement pur (GTA 6, matchs), sans valeur ici |
| Hacker News API | 200 | oui |
| GitHub search issues | 200 | oui — rate-limit ~10 req/min sans auth |
| `community.n8n.io/latest.json` | 200 | oui |
| Stack Overflow API | 200 | oui |
| FreeWork | 200 | oui |
| LinkedIn pages publiques | 200 | oui (annonces seulement) |
| Reddit `.json` · Indeed · Malt | 403 | non — aucun contournement tenté |

## Appariement skill ↔ tâche

- **bm25 ne discrimine pas.** Sur 400 titres : score −21,57 → `/content-perf-harvester`
  pour une tâche d'embeddings (faux) ; −16,77 → appariement juste. Le score seul est inutilisable.
- **Le recouvrement lexical discrimine**, à condition de le pondérer par emplacement :
  slug = 3 pts, nom = 2, description = 1.
- **Mots de 3 lettres = bruit** : `pre` appariait « Pre-remplissage » à « Pre-earnings ».
- **Vocabulaire de structure = bruit** : `triggers` appariait `/vue-dd-rum` à une tâche
  domino, parce que presque tous les SKILL.md contiennent « Triggers on mentions ».
- Distribution finale sur 500 titres : 4 % abstention, 66 % à 3-4 pts, 24 % à 5-6, 5 % à 7+.

## Superposition vectorielle (141 variantes, 18 cibles)

| Mesure | Valeur | Lecture |
|---|---|---|
| cos intra-cible | 0,885 | les angles collapsent facilement |
| cos inter-cible | 0,862 | 86 % de direction sémantique commune entre cibles |
| écart | +0,023 | la cible pèse à peine plus que l'angle |
| paires > 0,93 | 16 | l'angle n'a rien changé sur ces paires |
| `RECRUTEUR / DISPO` | 0,902 | **publipostage** — attendu : aucune matière sur ces cibles |
| `STARTUP / SIGNAL` | 0,810 | le plus personnalisé : il part du fait observé sur *eux* |
| `STARTUP / SOUVERAINETE` | 0,863 | le plus template : il parle de *nous* |

**Conclusion géométrique** : la part « moi / infra » écrase la part « eux ». Convergence
indépendante avec le verdict de la table ronde (« absence de preuve tangible ») et avec la
grille produit (« le message parle de l'atelier, pas du client »).

## Contraintes verbales vs physiques

La consigne « 280 caractères MAXIMUM » a été respectée **18 fois sur 45 (40 %)** — un LLM ne
compte pas les caractères. Remplacée par un budget de tokens (88) + troncature déterministe à
la dernière phrase complète : **51/51 conformes, max 277 c**. Une contrainte de forme se pose
mécaniquement, jamais verbalement.

## Dette découverte

| Constat | Mesure |
|---|---|
| Angle mort skills | `jarvis-plan.py:53` ne lit qu'une racine : 1 016 vus sur 40 073 (2,6 %) |
| Préchargement creux | 11 360 / 12 792 entrées valaient `{"ready_cmd": "dominos <slug>"}`, 84 c |
| Home fantôme | 898 blocs de `prechargement` pointent vers `/home/turbo` — **898/898 absents sur M4** |
| Doublons | `plan` : 12 792 lignes pour 4 781 titres distincts (63 % de doublons, jusqu'à 65 copies) |
| gstack absent | **26 skills** invocables dépendent d'un runtime introuvable sur tout le disque |
| planning-with-files | 9 copies installées, **toutes** avec `scripts/` et `templates/` vides |
| Chemins JARVIS | 101 existants / 36 absents dans les SKILL.md (74 % valides) |

## Volet C — trois pannes, trois natures différentes (19/08)

**1. M6 a redémarré (up 39 min) et LM Studio n'a pas été relancé.** Le moteur llama.cpp
tourne (PID 25534), les 4 GPU portent leurs modèles en VRAM (1,7 + 2,1 + 6,3 + 2,1 Go),
mais **rien n'écoute sur le port 1234**. Le watchdog `lms-watchdog/agent.py` (PID 3981)
tourne et n'a pas fait son travail. `lms server start` par SSH n'a pas rendu la main en 90 s.
Ping 1,4 ms, SSH et Ollama (11434) ouverts : M6 est joignable, c'est le service HTTP qui manque.

**2. Ollama M6 ne sert pas d'embeddings** (`gpt-oss:20b-cloud`, `qwen2.5:1.5b` seulement).
Ollama **M4 local** sert `nomic-embed-text` en 768 d — d'où la cascade.
Mesure : Ollama **sérialise** les embeddings (6 appels parallèles = 5,3 s chacun,
pas 0,9 s), donc le parallélisme n'apporte rien face à lui, contrairement à M6.

**3. Deadlock — mon bug.** `worker()` incrémentait le compteur sous `_lk` puis appelait
`log()`, qui reprend `_lk`. `threading.Lock` **n'est pas réentrant** : le thread se bloque
lui-même. Déclenchement exactement au 40ᵉ vecteur (`ok[0] % 40 == 0`), arrêt à 45
(40 + les 5 en vol). Signature au diagnostic : 7 threads endormis, **0 connexion réseau
ouverte**, 0 progression — un blocage réseau aurait laissé des sockets. Corrigé en `RLock`,
et vérifié par un test isolé : `Lock` réentrant = False, `RLock` = True.

**Garde-fou ajouté au passage** : `moisson_vecteurs` porte désormais le `backend` qui a
produit chaque vecteur, et `charger()` refuse de clusteriser un mélange — deux modèles
d'embedding placent le même texte à des endroits différents, et **aucun chiffre du
résultat ne signalerait le mélange**.

## Le bruit qui se faisait passer pour un pattern (19/08)

Le **cluster le plus dense de tout le corpus** — 13 membres, cohésion 0,914, le meilleur
score de la table — était composé à 77 % de **« Voir cette offre »**. Ma regex FreeWork
acceptait `(?:job|mission)`, donc elle capturait aussi les filtres de ville
(`/jobs/paris`) et le second `<a>` de chaque carte, dont le texte est un bouton.

Ce qui a tenu, et pourquoi ça compte :

- le **clustering était juste** — des textes identiques *doivent* avoir une cohésion de 0,91 ;
- le **modèle a refusé d'inventer** : 4 lectures sur 4 ont répondu `INSUFFISANT.`, exactement
  comme le prompt le prévoyait, au lieu de fabriquer un « besoin du marché » à partir de
  boutons de navigation.

Sans cette consigne, la chaîne aurait produit un pattern parfaitement présentable, avec la
meilleure cohésion du lot, entièrement faux. **La métrique la plus flatteuse du run était
celle du bruit.**

Ampleur mesurée : 51 signaux pollués sur 257 (20 %), dont FreeWork 26/39 (67 %).
Corrigé sur trois plans : extracteur ciblé sur `/job-mission/` uniquement, filtre de qualité
générique à l'insertion (appliqué à **toutes** les sources, et qui journalise ce qu'il écarte),
Google Trends sorti du jeu par défaut. Après correction : 428 signaux, **0 titre court**,
21 libellés de navigation écartés et comptés lors de la re-moisson.

## Volet C — le résultat principal n'est pas dans les patterns

**16/16 clusters étaient mono-source.** Aucun n'a jamais mélangé deux plateformes.
La matrice de similarité l'explique : la diagonale (interne à une source) domine partout
le hors-diagonale — freework 0,681 contre 0,393-0,481 ; n8n-forum 0,569 contre 0,456-0,504 ;
hacker-news 0,544 contre 0,382-0,477.

**L'embedding capture d'abord la façon d'écrire du site, ensuite le sujet.** Un cluster
mono-source n'est donc pas un signal de marché : c'est un signal de site. La vue de
restitution lève l'avertissement toute seule (`12/12 patterns exploitables sont MONO-SOURCE`).

**Correction appliquée** — centrage par source (soustraire à chaque vecteur le centroïde
de sa propre source, puis renormer). Effet mesuré : écart intra/inter **+0,110 → −0,011**.
Les sources ne sont plus séparables par leur style. Coût : zéro inférence, algèbre seule.

**Mais le centrage ne crée pas de signal absent.** Les clusters multi-sources qui émergent
se forment sur du recouvrement lexical superficiel :
`Consultant Sécurité IA` + `Beware Management Consultants` (le mot *consultant*),
un message portugais sur un certificat + une erreur `Input validation` (le mot *validation*).

**Conclusion honnête** : 428 signaux répartis sur 5 sources de natures différentes — offres
d'emploi françaises, forum n8n, issues GitHub, Hacker News, Stack Overflow — n'ont pas la
densité nécessaire pour qu'un besoin transversal émerge. Pour que la méthode donne un vrai
signal de marché il faudrait soit beaucoup plus de volume par thème, soit des sources de
même nature (n forums de même type plutôt que 5 canaux hétérogènes).

## Le motif qui revient

Trois fois ce soir, le même défaut sous des formes différentes :

1. `lm-ask.sh --big` — drapeau non parsé, parti dans le prompt : exit 0, sortie non vide, hors sujet.
2. Le préambule `/plan-tune` — chaque commande finit par `|| echo "<défaut>"` : aurait « réussi »
   en fabriquant un profil développeur entier sans une seule donnée réelle.
3. Le RSS Trends — `ON CONFLICT` écrasait 9 signaux sur 10, sans erreur.
4. Le deadlock `Lock`/`RLock` — 7 threads vivants, processus à l'état `S`, aucune
   exception, aucun log : le job avait *l'air* de travailler pendant qu'il ne faisait rien.
5. `| tail -24` sur un job de fond — la sortie paraissait vide parce que `tail` retient
   tout jusqu'à la fin du pipe. J'ai cru le job muet ; il écrivait dans son journal.

**Un code de retour 0 ne prouve rien.** Ce qui prouve, c'est une valeur qu'on peut recompter.
