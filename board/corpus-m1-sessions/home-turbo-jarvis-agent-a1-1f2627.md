[user] Tu crées un SKILL de documentation exécutable pour un outil interne. Tu ne connais rien de la conversation qui précède.

## Contexte

`/home/turbo/jarvis/board/` contient un « board d'experts » local et souverain, écrit en Python stdlib seule. Principe : une question entre, N experts du domaine répondent chacun avec SA grille de lecture (`lens`) **en citant** des extraits d'un corpus indexé, puis un arbitre synthétise. **Règle fondatrice : une réponse sans citation est invalide** — et c'est vérifiable en SQL, pas seulement demandé au modèle.

Fichiers :
- `board.py` — le CLI (init, domain add, expert add, ingest, embed, ask, status)
- `board_schema.sql` — 7 tables + FTS5
- `board.db` — SQLite (~93 Mo)
- `test_embed_diag.py` — 11 tests unitaires
- `pack-rem/charge-pack.py` — chargeur de packs d'experts (accepte `--pack CHEMIN`, `--apply`, `--force`)
- `pack-jarvis/experts-jarvis.json` — un pack d'experts

État réel mesuré : **9 domaines, 44 experts (9 arbitres), 40 633 chunks dont 3 291 vectorisés**. Répartition des chunks : `souverainete` 28 010, `cluster-m1` 9 662, `orchestration-agents` 1 528, `biblio-vivante` 1 433.

Stockage : SQLite + FTS5 (recherche lexicale BM25) **et** embeddings en BLOB float32 **dimension 768** (constatée, modèle `text-embedding-nomic-embed-text-v1.5` via LM Studio `127.0.0.1:1234`). `retrieve()` fusionne les deux voies par rang (RRF).

## Ta mission

Créer `/home/turbo/jarvis/.claude/skills/run-board/` avec **deux fichiers** :

### 1. `driver.sh` —

[assistant] LM Studio is up (200). Five domains have experts but zero corpus. Now let me write the driver.

[assistant] The DB grew mid-run (40 633 → 78 169 chunks). Let me check whether an ingest is actively running.

[assistant] Stable now — the growth was a concurrent ingest that has finished. Let me polish one confusing output block and capture the final verbatim run.

[assistant] Let me verify the failure path really returns 1, check usage exit code, and confirm the GPU temperature claim.

[assistant] Both files created and verified. No existing file was touched.

## Fichiers

- `/home/turbo/jarvis/.claude/skills/run-board/driver.sh` (exécutable, 15 Ko)
- `/home/turbo/jarvis/.claude/skills/run-board/SKILL.md` (11 Ko, frontmatter `name` + `description` uniquement)

## Sortie réelle de `driver.sh smoke` (verbatim, codes ANSI retirés)

Elle est recopiée intégralement dans `SKILL.md` — résumé des verdicts : les 9 familles de contrôles passent, avec 2 avertissements documentés (5 domaines peuplés d'experts mais sans corpus ; 4 réponses historiques dans `answers_sans_citation`). `Ran 11 tests — OK` pour `test_embed_diag.py`.

**Code de sortie : `0`.**

Chemins de défaillance vérifiés séparément sur une copie mutilée sous `/tmp` (vue supprimée + expert sans lens) : `SMOKE EN ECHEC`, **exit 1**. Usage vide et sous-commande inconnue : **exit 2**.

## Écarts avec l'énoncé, dits franchement

1. **Les chiffres du brief étaient déjà périmés.** L'énoncé annonçait 40 633 chunks / 10 681 sources ; j'ai mesuré 40 633 à 14:36, puis **78 169 chunks / 12 334 sources** à 14:37 — une ingestion concurrente (hors de mon contrôle) a doublé le corpus pendant mon travail. Stabilisé depuis (vérifié sur 25 s). La répartition a changé en proportion : `souverainete` 47 423, `orchestration-agents` 17 504, `cluster-m1` 11 024, `biblio-vivante` 2 218. Inchangés : 9 domaines, 44 experts (9 arbitres), 3 291 vectorisés, dim 768. J'ai documenté les chiffres **mesurés** et ajouté un avertissement explicite « ne