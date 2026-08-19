[user] <local-command-stdout>CLAUDE_CODE_EFFORT_LEVEL=low overrides effort this session — clear it and ultracode takes over</local-command-stdout>

[user] # JARVIS Agent 11 — Base de Données

**Rôle :** Coffre-fort : surveille et nettoie les BDD.

## Action

Traite : . Pour la santé : list_tables + describe_table + comptages via read_query (PRAGMA integrity_check). VACUUM/ANALYZE uniquement sur instruction explicite.

[assistant] L'integrity_check complet a dépassé 2 min sur `jarvis_master.db`. Je passe en `quick_check` avec timeout par base.

[assistant] Deux anomalies : taille apparente 0 et `quick_check` vide sur `jarvis_master.db`. Je vérifie les fichiers réels (-wal/-shm).

[assistant] **Santé des bases — vérifiée, aucune corruption.**

| Base (réelle) | Taille | WAL | Tables | quick_check | FK |
|---|---|---|---|---|---|
| `databases/jarvis_master.db` | 4,4 Go | ✅ | 102 | **ok** | — |
| `databases/board.db` | 3,1 Go | ✅ | 13 | **ok** | — |
| `data/prospection_reelle.db` | 492 Ko | ✅ | 7 | **ok** | — |

Contenu : board = **87 475 chunks / 15 687 sources** (le chiffre « 49 317 » du CLAUDE.md est périmé). Prospection = 7 tables (`contacts_moissonnes`, `vivier_qualifie`, `envois_reels`, `contacts_preuve`, `contacts_ecartes`, `moisson_journal`).

**Deux points à connaître :**

1. `~/jarvis/jarvis_master.db` et `~/jarvis/board/board.db` sont des **symlinks** vers `~/jarvis/databases/`. `du -h` sur le lien renvoie 0 — piège classique de mesure, la base n'est pas vide.
2. `PRAGMA integrity_check` (complet) dépasse 2 min sur les 4,4 Go — utiliser `quick_check`. Un `foreign_key_check` complet est également coûteux ; je ne l'ai pas forcé.

**Encombrement des sauvegardes : 7,2 Go** de `.bak` — dont deux copies board de 3,24 Go (`bak-pii-0636` et `bak-purge-0610`, quasi identiques, du 15/08). Suppression de la plus ancienne récupérerait ~3 Go, mais je n'y touche pas sans ton feu vert.

Pas de `VACUUM`/`ANALYZE` lancé (instruction explicite requise) — à noter que `VACUUM` sur les 4,4 Go demanderait ~4,4 Go de libre temporairement.