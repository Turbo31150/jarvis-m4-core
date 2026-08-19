[user] Tu diagnostiques une panne sur la machine `rem-linux` (poste Linux de Rémi, /home/rempc). Réponds en français.

## Le problème

Dans la base PostgreSQL `jarvis_main`, la table `memory_timeline` enregistre un résumé à chaque compaction de contexte Claude Code, sous `project='jarvis-ops'`, `event='precompact_summary'`.

- Les entrées id 615 et 616 (11/07/2026) ont le statut `COMPACTED` — c'est le fonctionnement normal.
- Les entrées id 625 (28/07), 629, 630, 631 et 632 (29-30/07) ont le statut **`ERROR`**.

Le hook de résumé pre-compact est donc cassé depuis fin juillet. Conséquence : à chaque compaction, du contexte est perdu silencieusement.

## Accès aux données (important)

`psql` n'existe PAS sur cet hôte. PostgreSQL tourne dans un conteneur sur une AUTRE machine (la « tour »), joignable uniquement par Tailscale en root :

```bash
ssh root@100.124.69.1 "docker exec jarvis-postgres psql -U jarvis -d jarvis_main -c \"<SQL>\""
```

Pour du SQL multi-lignes, écris un fichier et pipe-le :
```bash
ssh root@100.124.69.1 "docker exec -i jarvis-postgres psql -U jarvis -d jarvis_main -A -F'|'" < /tmp/req.sql
```

## Ta mission

1. Trouve le script du hook. Point de départ probable : `/home/rempc/.claude/hooks/precompact-jarvis-summarize.sh` — mais vérifie aussi `~/.claude/settings.json` et `~/.claude/settings.local.json` pour savoir quel hook est réellement câblé sur l'événement PreCompact.
2. Lis le script et identifie ce qui écrit le statut `ERROR` plutôt que `COMPACTED`.
3. Cherc

[assistant] I'll start by loading the context-mode tools and investigating the hook configuration.

[assistant] Key finding already: the hook never writes "ERROR" itself — it comes from the Python script. Let me dig into that and the DB.

[assistant] Now let me pin down the ERROR cause precisely and check the DB around those IDs.

[assistant] Decisive evidence emerging. Let me check the routing path and probe the exact response shape.

[assistant] Rapport écrit dans `/home/rempc/bibliotheque-vivante/rapports/diag-precompact.md`. Aucun fichier existant modifié, aucune correction appliquée.

## Ce que j'ai trouvé

**Deux corrections du postulat d'abord :** id 629 n'est pas un `precompact_summary` (c'est `project='flow'`, status `done`), et la première ligne en ERROR est **id 542 du 17/06**, pas le 28/07.

**1. Hook et ligne fautive**

Câblé dans `~/.claude/settings.json:180-185` (pas de `settings.local.json`) → `/home/rempc/.claude/hooks/precompact-jarvis-summarize.sh`. Le hook n'écrit jamais `ERROR` lui-même : il recopie `.status` du Python. La ligne d'origine est `/home/rempc/jarvis/scripts/utils/jarvis-ctx-summarize.py:180` (`OpenClaw bad response`), levée par le `raise RuntimeError` de la ligne 102.

**2. Cause racine — ce n'est PAS la migration**

Les ERROR datent du 17/06 et 28-30/07 ; la migration date du 03/08 21:50 (mtime des units `jarvis-bridge-*`, conteneurs locaux stoppés à 19:49Z). Elle est postérieure.

La vraie cause : `orchestrator.js:440` → `MODEL_MAP.code = "qwen3-coder-next"`, **retiré par ollama.com le 2026-07-15**. Sonde live :
```
{"error":"qwen3-coder-next was retired at 2026-07-15 00:00:00 -0700 PDT"}
```
Le code contient déjà un contournement pour `gemma3:27b`/`12b` retirés le même jour — `MODEL_MAP.code` a été oublié. Conséquence : l'appel cloud ne renvoie pas de `content`, OpenClaw tombe en cascade sur `cowork/dispatch` qui répond `{matches, query, latencyMs, score}` **sans champ `response`** 