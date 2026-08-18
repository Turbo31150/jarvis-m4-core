[assistant] Je commence par sonder l'existant et les capacités réelles de la machine avant de trancher quoi que ce soit.

[assistant] Corpus réel : 47 046 lignes, 8,6 Mo, FTS5 disponible. Je sonde maintenant le moteur candidat et l'existant.

[assistant] FTS5 : index en 0,16 s, requêtes à 0,3–2,3 ms. Je mesure maintenant le coût réel du vectoriel et je vérifie les projets.

[assistant] Vectoriel : 12 min d'indexation. Je vérifie l'alternative sans dépendance et je teste la qualité de rappel.

[assistant] Je mesure maintenant le taux réel de pourriture du corpus — le chiffre qui dimensionne la migration.

[assistant] Dernier contrôle : l'effet d'une stoplist française sur FTS5, avant de trancher.

[assistant] Étude terminée — tout est mesuré sur la machine, aucun fichier modifié, rien installé.

---

# AVALER ET REFABRIQUER — bibliothèque vivante JARVIS

## 0. Mesures de départ (faites, pas estimées)

| Sonde | Résultat |
|---|---|
| `sqlite3` | 3.45.1 — **FTS5 OK** (CLI et module Python) |
| Corpus réel | **47 270 blocs**, 8,6 Mo, 4 colonnes, 26 sources (`commande-directe` 12 912, `github-jarvisos` 7 467, `script` 6 862…) |
| `sqlite_vec` / `usearch` / `hnswlib` / `faiss` | **tous absents** — `numpy` et `sklearn` présents |
| LM Studio :1234 | `qwen/qwen3.5-9b`, `text-embedding-nomic-embed-text-v1.5` (**dim 768**), `openai/gpt-oss-20b` |
| `shellcheck` / `bashate` / `shfmt` | **absents** · `jq`, `rg`, `fzf`, `sqlite3` présents |

**Santé du corpus — le chiffre qui commande tout le plan :**

| Défaut mesuré | Volume |
|---|---|
| Blocs citant ≥1 chemin absolu | 23 750 (50,2 %) — dont **1 777 chemins morts (7,3 %)** |
| Blocs dont le binaire de tête est **introuvable** | **14 592 / 37 152 (39,3 %)** |
| **Blocs suspects (union)** | **14 793 = 31,3 % du corpus** |

Les binaires fantômes les plus fréquents sont `Analyse` (375), `Agent` (284), `generate_command` (228), `Configuration` (186), `Optimisation` (168) : **ce ne sont pas des commandes, c'est de la prose française** produite par le daemon LLM et rangée dans une colonne `bloc` censée contenir du shell exécutable. Le défaut est confirmé et quantifié.

---

## 1. Le choix du moteur de rappel

Tout mesuré sur les 47 045 blocs rée

[assistant] Nouveaux faits reçus — dont un qui contredit ma lecture. Je re-mesure sur l'index actuel avant d'envoyer, plutôt que d'arbitrer à l'aveugle.

[assistant] GPU0 : seulement **2,6 Go libres** sur 12 (qwen3.5-9b occupe 9,6 Go). Je re-mesure la taxonomie sur l'index actuel pour réconcilier mes chiffres avec ceux de l'audit.

[assistant] Ma taxonomie indépendante confirme l'audit. Je vérifie la commande de démarrage avant de la recommander.

[assistant] Rapport envoyé à `main`. Résumé de ce qui a changé par rapport à ma première analyse :

**J'avais tort sur un point, et je l'ai corrigé.** Mes « 39,3 % de binaires introuvables » n'étaient pas des hallucinations : ce sont des mots français (`Analyse`, `Configuration`) — des non-commandes. Ma reclassification indépendante des 50 957 blocs retombe sur ton audit à quelques points près (exec 16,6 % vs 12,8 %, templates 18,7 % vs 26,4 %, xdg-open 16,0 % vs 17,5 %, gh 15,0 % vs 16,4 %). Diagnostic confirmé : **non exécutable, pas halluciné**.

**Deux nuances factuelles maintenues :**
- 1 776 chemins absolus cités sont morts (6,4 % de 27 861). Ton échantillon de 60 n'en a vu aucun — statistiquement compatible (j'en trouve 2 sur un tirage de 60), mais 60 blocs n'ont pas la puissance de trancher à 6 %. Défaut réel, pas prioritaire.
- **Fait neuf : l'index grossit en direct.** 47 270 → 50 926 → **58 200** pendant la session. La part de blocs exécutables se dilue pendant qu'on en parle.

**GPU0 vérifié : 2,6 Go libres seulement** (qwen3.5-9b occupe 9,6 des 12 Go). nomic-embed tient (274 Mo), **un reranker cross-encoder ne tient pas** — ça élimine d'office le reranking neural.

**Moteur tranché : SQLite FTS5.** 0,16 s d'indexation, 0,3–2,3 ms par requête, 16,4 Mo, zéro dépendance, zéro VRAM. J'ai reproduit ton mode d'échec et vérifié que BM25 le corrige. `sqlite-vec` écarté (pre-v1 + ANN alors que le brute-force numpy est exact en 9,6 ms).

**Plan réorienté** : il ne filtre plus des hall