[user] Tu fais une REVUE DE QUALITÉ de code. Tu ne connais rien de la conversation qui précède. **Tu ne modifies AUCUN fichier** — tu lis, tu juges, tu rapportes.

## Le fichier à relire

`/home/turbo/jarvis/board/board.py` — CLI Python en stdlib seule (~420 lignes), sans dépendance externe. Lis-le en entier.

C'est le moteur d'un « board d'experts » local : un corpus est découpé en *chunks* dans SQLite (`board.db`), vectorisé via LM Studio (`http://127.0.0.1:1234/v1`), puis interrogé. Sur une question, N experts répondent chacun avec sa grille de lecture (`lens`) en citant des extraits, et un arbitre synthétise. Règle fondatrice du produit : **une réponse sans citation est invalide**, et cette règle est vérifiable en SQL (vue `answers_sans_citation`).

État réel : 40 633 chunks, 3 291 vectorisés, 9 domaines, 44 experts. Le fichier tourne en production sur cette machine.

## Ce qui vient d'être ajouté (déjà revu pour conformité — ne re-juge pas le périmètre)

- `class Embedding(list)` + `def embed(text, tentatives=2)` : distingue les causes d'échec (`timeout`, `reseau`, `http_<code>`, `reponse_illisible`, `dimension`) et réessaie **une seule fois**, uniquement si transitoire.
- `def gpu_temp_max()` : lit `nvidia-smi`, renvoie `None` si absent (fail-safe volontaire).
- `cmd_embed()` : découpage explicite en lots, commit incrémental par lot, arrêt si température ≥ `GPU_TEMP_MAX` (89), ventilation des échecs par cause.
- Dans `retrieve()`, le `except sqlite3.OperationalError` n'avale p

[assistant] Maintenant je vérifie certaines hypothèses contre la base réelle (lecture seule) et je lance les tests existants.

[assistant] J'ai lu le fichier en entier, exécuté la suite de tests existante (11/11 OK), mesuré le comportement réel de `chunk_text`, et interrogé `board.db` en lecture seule. Voici la revue.

---

# Revue de qualité — `board.py`

Vérifications faites : `test_embed_diag.py` → **11/11 OK**. Base réelle : 77 962 chunks (pas 40 633 — l'ingestion a continué), 3 291 vectorisés, tous en dim 768 / même modèle, FTS synchrone (77 962 lignes), 13 réponses dont 4 sans citation.

## BLOQUANT

**1. L378-379 — la panne de vectorisation est totalement muette (le pire piège du fichier)**
`qv = embed(question)` ; `if qv:`. Si LM Studio est arrêté ou renvoie 500, `qv` est falsy et la voie vectorielle est **silencieusement supprimée** — alors que dix lignes plus haut la panne lexicale, elle, est annoncée à l'écran avec un commentaire expliquant qu'il ne faut « JAMAIS avaler en silence ». Le board répond quand même, cite, et rien nulle part ne dit que la moitié du retrieval était morte. Pire : `Embedding.cause`, qui vient d'être ajouté précisément pour ça, n'est pas lu ici.
*Scénario* : LM Studio redémarre pendant une session → `ask` sort une réponse BM25-seule, plausible, avec citations, indistinguable d'une bonne réponse.
*Corollaire* : si les deux voies tombent, L428 imprime « aucun extrait du corpus ne correspond » — un diagnostic **faux** qui accuse le corpus alors que le backend est mort.
→ *Correctif* : `if qv: … else: print(f"  ! voie vectorielle HORS SERVICE ({qv.cause}: {qv.detail}) — RRF sur le 