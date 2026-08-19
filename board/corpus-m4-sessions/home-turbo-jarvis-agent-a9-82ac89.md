[user] Contexte : environnement JARVIS fraîchement (re)provisionné — des unit files systemd existent mais les scripts qu'ils référencent (ExecStart=) n'ont jamais été écrits sur cette machine. Tu dois RECONSTRUIRE ces scripts, de façon sûre et non destructive.

Écris exactement ces fichiers (bash, exécutables chmod +x), sachant que LM Studio tourne en local sur 127.0.0.1:1234 (API OpenAI-compatible), CLI `lms` disponible dans PATH :

1. `/home/turbo/jarvis/scripts/lms-sentinelle.sh` — vérifie que le serveur LM Studio répond (`curl -s --max-time 3 http://127.0.0.1:1234/v1/models`), si non : `lms server start`. Log dans `/home/turbo/jarvis/logs/lms-sentinelle.log` avec timestamp. exit 0 toujours.

2. `/home/turbo/jarvis/scripts/lms-auto-load-dual.sh` — vérifie via `lms ps` si au moins un modèle de chat (pas juste l'embedding "text-embedding-nomic-embed-text") est chargé ; si non, charge-en un avec `lms load <premier modèle chat trouvé via lms ls> -y --context-length 8192` (timeout raisonnable, ne bloque pas indéfiniment — utilise `timeout 90 lms load ...`). Log dans `/home/turbo/jarvis/logs/lms-dual-warm.log`. exit 0 toujours même si aucun modèle chat trouvé (log un warning).

3. `/home/turbo/jarvis/bin/skillmp-sentinelle.py` — python3, accepte le flag `--once` (argparse), vérifie l'existence et la fraîcheur (mtime < 24h) d'un registre de skills quelconque sous `~/.claude/skills/` (juste compte le nombre de dossiers dans `~/.claude/skills/`), log un résumé JSON dans `/home/turbo/jarvi

[assistant] Now retest with the fix. Currently only one embedding model exists on this machine, so no chat model is downloadable — script should correctly log a warning and exit 0.

[assistant] Correct now. exit=0, warning logged as spec requires since no chat model exists on this machine (only the embedding model is downloaded).

DONE

Files created (all executable, all `mkdir -p` their log dirs, all exit 0 unconditionally):
- `/home/turbo/jarvis/scripts/lms-sentinelle.sh`
- `/home/turbo/jarvis/scripts/lms-auto-load-dual.sh`
- `/home/turbo/jarvis/bin/skillmp-sentinelle.py`

Test results:
1. `lms-sentinelle.sh` — ran, LM Studio server already responding (HTTP 200), logged OK to `/home/turbo/jarvis/logs/lms-sentinelle.log`, exit 0.
2. `lms-auto-load-dual.sh` — ran with `timeout 100`. Found via `lms ps`/`lms ls` that this machine has only 1 model downloaded (`text-embedding-nomic-embed-text-v1.5`), no chat model available to load. Logged WARN and exited 0, per spec ("exit 0 toujours même si aucun modèle chat trouvé"). Note: had to fix parsing twice during testing — `lms ls`'s header line ("You have N models, taking up X MB...") was initially matched as a model row; added an explicit `grep -viE "^You have"` filter to exclude it. Logic now correctly parses real model rows by requiring a size column (MB/GB) while excluding the summary header and the embedding model.
3. `skillmp-sentinelle.py --once` — ran, found `~/.claude/skills/` with 461 subdirectories, most recent mtime 18.87h old (< 24h → fresh), logged JSON summary to `/home/turbo/jarvis/logs/skillmp-sentinelle.log`, exit 0.

Self-review notes: all three scripts are idempotent (safe to re-run), all network/lms call