[assistant] L'ingesteur tourne bien — mais pas dans la base qu'on croit. Vérifions le contenu.

[assistant] Écart intrigant : 12 697 doublons dans le JSONL mais la table en compte plus que les clés uniques. Vérifions.

[assistant] **Livrable** : `/home/turbo/jarvis/artifacts/e1-20260806/chantier-ingesteur-log.md`

L'ingesteur n'a jamais dormi — le constat de départ est à corriger.

- **Chemin** : `/home/turbo/jarvis/scripts/cascade-log-ingest.py` (intact, la refonte `scripts/` → `infra/scripts/` ne l'a pas touché ; le `SKILL.md` documente le bon chemin).
- **Pourquoi on ne le voyait pas** : collision de noms. Il écrit dans `/home/turbo/jarvis/data/jarvis_master.db` (18 Mo, base satellite), pas dans `/home/turbo/jarvis/jarvis_master.db` (3,3 Go). Chercher la table dans la master renvoie légitimement « absente ».
- **Preuve qu'il tourne** : `jarvis-cascade-ingest.timer` enabled depuis le 25/06 09:50, dernier déclenchement il y a 52 s, 126 runs journalisés, zéro échec, zéro `database is locked`.
- **Ingéré** : 144 413 lignes, du 25/06 05:55 au 06/08 12:21. 0 erreur de parsing. Idempotence vérifiée dans le code (curseur `ingest_state` + `INSERT OR IGNORE`) puis en réel : 2ᵉ passage = 0 insertion, 0,06 s.
- **Intégrité** : 3 lignes prélevées (positions 10 / 50 000 / 144 000) identiques au caractère près, NULL préservés. Réserve : `UNIQUE(ts,via,served,ms)` ne dédup pas quand `served` est NULL (49,4 % des lignes) — mais les 12 673 doublons sont déjà dans le JSONL source, la table est fidèle.

**p50 / p95 par backend (succès seuls, ms)** : `ollama/gemma3:4b` 30 014 / 132 096 (26 470 appels) · `lmstudio-node10/qwen3.5-9b` 11 512 / 38 859 · `ollama/qwen3:1.7b` 7 393 / 56 538 · `lmstudio-local` 28 828 / 65 448 ·

[assistant] Cette assignation (horodatée 12:23) est antérieure au travail — la tâche #17 est déjà terminée. Je signale le résultat au team-lead.

[assistant] Tâche #17 déjà terminée avant l'arrivée de cette assignation — résultat transmis au team-lead.

**Livrable** : `/home/turbo/jarvis/artifacts/e1-20260806/chantier-ingesteur-log.md`

Les deux prémisses de la tâche étaient fausses :

1. **L'ingesteur n'a jamais dormi.** `/home/turbo/jarvis/scripts/cascade-log-ingest.py` tourne toutes les 15 min depuis le 25/06/2026 09:50 — 126 runs journalisés, zéro échec.
2. **La cible n'est pas la base de 3,3 Go.** Collision de noms : il écrit dans `data/jarvis_master.db` (18 Mo, satellite), pas `jarvis_master.db` (3,3 Go). La contrainte `busy_timeout ≥ 120 s` ne s'appliquait donc pas — aucune contention, ingestion en 70 ms.

**Chiffres** : 144 413 lignes en table (25/06 05:55 → 06/08 12:21), 0 erreur de parsing, idempotence vérifiée dans le code puis en réel (2ᵉ passage = 0 insertion). Échantillon à 3 positions écartées identique au caractère près.

**p50/p95 par backend (succès seuls, ms)** : `ollama/gemma3:4b` 30 014 / 132 096 · `lmstudio-node10/qwen3.5-9b` 11 512 / 38 859 · `ollama/qwen3:1.7b` 7 393 / 56 538 · `lmstudio-local` 28 828 / 65 448 · `lmstudio-m1` 21 689 / 88 556 · `deepseek-r1:7b` 35 107 / 217 900.

Trois faits que le SQL rend enfin visibles : juillet à **48 % de succès** sur 129 696 routages ; le backend le plus sollicité est **2,6× plus lent** que son concurrent direct ; le repli est le chemin habituel (**63,7 %**).

Rien installé, rien modifié — timer non touché, JSONL intact.