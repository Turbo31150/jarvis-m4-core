[assistant] Premiers résultats collectés. Le conteneur Postgres `cmdlib` semble absent — je creuse.

[assistant] Le conteneur `commande_directe_bibliotheque-db-1` est absent et deux services Swarm bouclent en crash. Je vérifie qui sert le port 5432.

[assistant] Je vérifie la base cmdlib annoncée et l'écart entre tâches "done" et "done vérifiées".

[assistant] Découverte importante : 500 000 tâches "done" ne sont que 5 titres dupliqués 100 000 fois. Je vérifie la base cmdlib et le planning unifié.

[assistant] Audit terminé, tout en lecture seule. Voici le rapport.

## Rapport d'audit — bibliothèque vivante et planning JARVIS (M1, 2026-08-01)

### En une phrase

L'infrastructure de blocs et de séries est **réelle et fonctionnelle** (40 334 blocs indexés, routeur opérationnel, 197 séries, 5 529 dominos compilés), mais **la base Postgres `cmdlib` annoncée n'existe plus** (conteneur absent, volume orphelin de 80 Mo) et **le planning est saturé de tâches artificielles** : sur 2 098 481 tâches "done", 500 000 sont 5 titres dupliqués 100 000 fois chacun, et seulement 4,5 % sont vérifiées.

---

### 1. Index de blocs — EXISTE, plus gros que documenté

`/home/turbo/labo/bibliotheque/lib/BLOCS-INDEX.tsv` : **40 335 lignes** (40 334 blocs + en-tête), 7,4 Mo. Qualité structurelle bonne : **0 doublon** (nom, source) et **0 ligne malformée** (toutes à 4 colonnes).

Répartition par source (top 12) :

| Source | Blocs | Source | Blocs |
|---|---|---|---|
| commande-directe | 10 014 | ocow-script | 1 290 |
| github-jarvisos | 7 469 | cmd-directe | 551 |
| script | 5 334 | tool-map | 446 |
| doc | 4 312 | service | 351 |
| report | 3 877 | openclaw | 296 |
| sql | 2 743 | ocow-doc | 251 |

Il y a 109 fichiers `lib/*-blocs.tsv` totalisant 43 831 lignes, soit environ **3 400 blocs présents dans les fichiers unitaires mais absents de l'index central** — la fusion n'est pas complète. Le répertoire `lib/` pèse 75 Mo dont 15 sauvegardes `.bak` de l'index (jusqu'à 7 Mo pièce).

**Écart doc ↔ réalité** : l

[assistant] Deux points de son message contredisent mes mesures — je revérifie avant de conclure.

[assistant] Le conteneur `jv-infra-biblio-db` a été ranimé pendant mon audit (up depuis 11 min) — il était bien absent à 16h50. Je confirme les comptes en lecture seule.

[assistant] Rapport final ci-dessous. Deux de tes constats sont à corriger — je les mets en tête.

## Audit bibliothèque vivante + planning — M1, 2026-08-01

**Deux corrections sur tes chiffres**

1. **`/data` répond aussi**, et c'est l'endpoint riche : HTTP 200, **299 606 octets** (23 sections : counts, dominos, agents, routing, n8n, frontieres, unified, strategie…). `/api/production` répond 200 mais **722 octets** seulement. Les deux sont vivants ; `/data` est celui qui porte les données.
2. **`jv-infra-biblio-db` était ABSENT** de `docker ps -a` à 16h50 — aucun conteneur biblio, seulement deux volumes orphelins (`commande_directe_bibliotheque_cmdlib_pg`, 80 Mo) et l'image `commande_directe_bibliotheque-web`. Il a été **ranimé pendant mon audit** (up depuis 11 min à 17h09). Je confirme tes comptes sur la base ranimée : `commands` **10 246**, `holding_index` **0**, `library_series` **0**. Le conteneur `commande_directe_bibliotheque-db-1` du brief n'a jamais existé.

**Bases SQLite**

| Base | Taille | Tables |
|---|---|---|
| `~/jarvis/jarvis_master.db` | 1,8 Go | 63 |
| `~/jarvis/data/unified_plan.db` | **1,7 Go** | 3 |
| `~/jarvis/cowork_engine.db` | 38 Mo | 3 |
| `~/jarvis/data/etoile.db` | 2,0 Mo | 13 |
| `~/jarvis/logs/jarvis_logs.db` | 540 Ko | 6 |

Tables les plus volumineuses de `jarvis_master.db` : `tasks` 2 098 543 · `full_disk_m6_index` 1 367 314 · `home_full_scan` 1 292 545 · `disk_index` 386 145 · `pipeline_log` 254 203 · `biblio_topics` 78 934 · `chat_sessions` 40 720 · `d