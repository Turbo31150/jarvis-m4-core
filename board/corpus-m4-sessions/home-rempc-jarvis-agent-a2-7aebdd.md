[user] Tâche mécanique en 2 livrables, spec fermée, aucune initiative hors spec.

LIVRABLE 1 — Patch de /home/rempc/.claude/hooks/tdai-preflight-grep.py (125 lignes, hook UserPromptSubmit, doctrine ABSOLUE : fail-silent, ne JAMAIS pouvoir casser la session).

CONTEXTE DU BUG À RÉPARER : ce hook injecte les atoms mémoire par pertinence RRF uniquement. Les CORRECTIFS récents (petits atoms datés qui supersèdent des morceaux de gros atoms) sont mal classés par pertinence → 2 erreurs de mémoire périmée le 2026-08-02. Fix : ajouter un balayage par RÉCENCE.

SPEC EXACTE :
1. Lis d'abord le fichier en entier (125 lignes) pour comprendre la structure (fonction search(), formatage des résultats, cap MAX_CHARS, log_fire).
2. Après que les résultats RRF retenus sont connus (ids + scopes), ajoute une étape "recency sweep" :
   - Collecte les scopes DISTINCTS des atoms RRF injectés.
   - Si aucun scope → skip silencieux.
   - Une SEULE requête Postgres via la constante PSQL existante :
     SELECT id, scope, created_at::date, left(regexp_replace(content, E'\n+', ' ', 'g'), 160)
     FROM memory_atoms
     WHERE scope = ANY(ARRAY[<scopes quotés>])
       AND created_at >= NOW() - INTERVAL '14 days'
       AND id != ALL(ARRAY[<ids déjà injectés quotés>])
     ORDER BY created_at DESC LIMIT 4;
     Échappe les apostrophes des scopes/ids (s.replace("'", "''")).
   - timeout subprocess 3s, tout dans try/except Exception → skip silencieux.
3. Si résultats : appends au texte injecté une section :
   "# 

[assistant] Test réel réussi, exit 0, section recency sweep présente avec atoms du 2026-08-02. Test fail-silent:

[assistant] Rapport final (max 15 lignes) :

**Diff** — `/home/rempc/.claude/hooks/tdai-preflight-grep.py` : +1 fonction `recency_sweep(scopes, injected_ids)` (avant `main()`, ~30 lignes, requête PSQL unique/timeout 3s/try-except silencieux) ; dans `main()` collecte `injected_scopes`/`injected_ids` pendant la boucle RRF existante, appel `recency_sweep()`, append section "# Correctifs récents..." bornée par `MAX_CHARS`, ajout `recency_count` au `log_fire`. Aucun autre changement.

**Tests** :
- a. `ast.parse` → `AST_OK`
- b. Run réel (sidecar :3250 up) → exit 0, JSON valide, section recency sweep présente avec 4 atoms scope `cession_soleil` datés `2026-08-02` (ex. `atom_cession_karim_banquier_ok_verbal_misept_20260802`)
- c. `TDAI_SIDECAR_URL=http://127.0.0.1:9` → `EXIT=0`, aucun crash (fail-silent confirmé)

**Postmortem** : `/home/rempc/jarvis/docs/postmortems/2026-08-02-stale-memory-2x-sweep-fix.md`

Aucune question non-triviale remontée — spec exécutée telle quelle.