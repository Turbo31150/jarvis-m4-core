[user] Tu travailles dans le dépôt /home/rempc/jarvis. Tu crées UN SEUL fichier neuf : `scripts/harvest/extract-keywords.py`. Ne modifie aucun fichier existant.

CONTEXTE — le corpus existe déjà, il a été moissonné aujourd'hui :
- Staging SQLite : `~/jarvis/data/harvest/cli-conversations.sqlite3` (20 Mo). Tables : `sessions(uid, source, session_id, project, title, started_at, ended_at, n_messages, n_chars, src_path)` et `messages(session_uid, idx, role, ts, text, truncated)`, plus une table FTS5 `messages_fts(text, session_uid, idx)`.
- Contenu : 186 sessions / 7423 messages / 6,3 Mo de texte, en FRANÇAIS majoritairement (avec du technique en anglais), du 15/04 au 07/08/2026. Sources : `gemini-chats`, `gemini-legacy`, `agy-convos`, `agy-history`.
- Les mêmes données sont aussi dans Postgres, schéma `cli_harvest` — mais Postgres tourne sur une AUTRE machine (tour, accès `ssh root@100.124.69.1 "docker exec jarvis-postgres psql -U jarvis -d jarvis_main ..."`). Pour ce script, travaille sur le SQLite local : c'est plus simple et suffisant.

TÂCHE : écrire un extracteur de mots-clés qui répond à la question « de quoi Rémi a-t-il réellement parlé avec ses CLI, et quand ».

Exigences :
1. Extraction de termes saillants par TF-IDF (ou BM25) calculé en Python pur / stdlib + éventuellement `collections`. N'installe AUCUNE dépendance externe : ni sklearn, ni nltk, ni spacy. La machine est un i7 8 cœurs 15 Go, le corpus fait 6,3 Mo, du pur Python suffit largement.
2. Une liste d'arrêt FRANÇAISE

[assistant] I'll start by examining the existing script for style conventions and the SQLite staging DB.

[assistant] Noise. The IDF explodes on rare boilerplate repeated inside a few sessions. Let me fix the weighting: saturate TF *per session* (so a re-injected system prompt counts once-ish), then use linear TF-IDF.

[assistant] Still dominated by tool-call machinery (`toolsummary`, `commandline`, `waitmsbeforeasync`). Those are harness identifiers leaking from tool payloads. Fixing at the tokenizer level.

[assistant] Bigrams are strong. Fixing residual artifacts: `\n`-escapes glued to words (`nimport`, `nprint`), trailing hyphens (`bot-`), and a few remaining generic tokens.

[assistant] SHA256 identical, no WAL/journal left behind. One artifact remains in July — a cluster of misspellings all at exactly freq 41. Let me verify what it actually is before judging.

[assistant] Confirmed: that cluster is a real user directive Rémi retyped verbatim ~40 times in July (typos included), not an extractor artifact. Final checks.

[assistant] One real weakness left: `gemini-chats` is 80% Gemini CLI preamble (identical text re-injected each session). Let me add generic line-level boilerplate stripping.

[assistant] Only 8 lines caught — the Gemini preamble isn't line-aligned. Let me look at the actual text.

[assistant] The preamble is a pseudo-XML `<session_context>` envelope whose contents vary per session. Adding generic envelope stripping plus digit-masked line matching.

[assistant] `gemini-chats` shrank by two thirds. The residual is another per-CLI preamble. Boilerplate detection should be scoped per source — each CLI has its own preamble.

[assistant] June lost 36% of its volume — the per-source threshold may be over-stripping small sources. Adding a floor so tiny sources aren't over-pruned.

[assistant] Boilerplate lines went 187→22 with no loss on the month axis (June's reduction came from envelope stripping, not line pruning). Fixing a stale comment reference, then final validation.

[assistant] Livré.

## Fichier

**`/home/rempc/jarvis/scripts/harvest/extract-keywords.py`** — seul fichier créé, aucun fichier existant modifié. Pur stdlib (`argparse`, `sqlite3`, `re`, `math`, `unicodedata`, `collections`), ~4,5 s sur les 6,3 Mo.

Staging inchangé, vérifié au sol : `0ccc6d0e…d7030a4ad76` avant **et** après les trois runs, aucun `-wal`/`-journal` créé (ouverture `file:…?mode=ro`, `uri=True`).

## Sorties réelles

**`--global`** (`186 sessions · 17203 termes · df>=6 freq>=5 · 22 lignes de gabarit écartées`)

```
  1. docker    116.75  freq 941   2. agent   115.85  freq 700   3. python3  114.75  freq 905
  4. audit     114.12  freq 906   5. jarvis  113.64  freq 1838  6. check    112.70  freq 785
  7. board     111.98  freq 777   8. gemini  110.86  freq 1061  9. dva      110.80  freq 491
 10. psql      109.23  11. skills 108.51  12. git 108.24  13. mcp 107.31  14. postgres 107.20
 15. skill     106.43  16. jarvis-postgres 106.07  17. agents 105.77  18. plan 105.70
 19. memory    105.50  20. select 105.08  21. test 104.94  22. claude 104.80  23. session 104.60
 24. code      103.72  25. cli 102.32  26. execution 102.11  27. api 102.02  28. remi 101.37
 29. error     101.08  30. application 100.96
```

**`--par-mois`** (tête de chaque mois, sortie complète ci-dessus dans la session)

| mois | sessions | tête du classement |
|---|---|---|
| 2026-04 | 3 | domino, omega, cowork, cluster, chain, dispatch, routage, compact, archi |
| 2026-05 | 55 | dva, cron, psql, hook, diff, dr