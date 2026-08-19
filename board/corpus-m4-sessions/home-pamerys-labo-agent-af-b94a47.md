[user] CONTEXTE MACHINE (verifie, ne pas re-supposer) :
- Tu es sur M4, hostname pamerys-m4, uid=1000(pamerys), HOME=/home/pamerys.
- /home/turbo N'EXISTE PAS sur M4. C'est le home de la machine M1. Son contenu est
  accessible en LECTURE via le SSD USB monte : /media/pamerys/JARVIS-M1/home/turbo
- /home/rempc N'EXISTE PAS non plus (autre machine).
- INTERDIT : la commande `docker` en local frappe une pile PERIMEE (incident 2026-08-11,
  ecritures silencieusement perdues). Un hook la BLOQUE. Utilise toujours
  /home/pamerys/jarvis/bin/jarvis-docker qui route vers la tour (root@100.124.69.1).
- Journal des skills : /home/pamerys/jarvis/db/cli_history.db, table skill_invocations
  (colonnes : id, session_id, skill_name, invoked_at, trigger_phrase, outcome, feedback_score).
- Backends LLM 0-token disponibles : hub unifie http://127.0.0.1:18800/v1 (modeles logiques
  jarvis-fast / jarvis-auto / jarvis-quality), LM Studio M6 http://10.42.0.230:1234/v1
  (qwen/qwen3.5-9b), Ollama local http://127.0.0.1:11434 (gemma3:4b).
  ATTENTION : LM Studio ne tourne PAS sur 127.0.0.1:1234 de M4 — c'est M6.
- Board d'experts local : /home/pamerys/jarvis/board/board.py (usage : board.py ask <domaine> "<question>").
  Scripts prets : /home/pamerys/jarvis/board/ask-hub.sh et ask-m6.sh.

REGLES ABSOLUES :
1. AUCUNE action sortante reelle. Pas d'envoi de mail, pas de publication LinkedIn /
   Instagram / TikTok / YouTube / Notion, pas d'ordre de trading, pas de push git.
   Si le skill a une fonction de pu

[assistant] Confirmed: `/home/turbo` hardcoded everywhere, and `driver.sh` returns rc=0 despite total failure. Let me map the real M4 equivalents.

[assistant] Now I'll vendor the secrets scanner into the skill (M4 has none; the original lives read-only on the M1 SSD).

[assistant] Now the entry point `run.sh`, which was a dead stub pointing at `/home/turbo/alkymia`.

[assistant] The scanner resolved to `$JARVIS_HOME/bin/scan-secrets.sh`, which did **not** exist earlier. Let me verify what happened.

[assistant] A concurrent sibling agent installed its own `scan-secrets.sh` into `jarvis/bin` at 09:42; my resolution order correctly prefers it over my vendored fallback. Let me fix a real collision bug I spotted (two runs in the same minute overwrite the same report) and then test the fallback paths.

[assistant] Now testing the fallback and failure paths in isolation, without touching the real JARVIS tree.

[assistant] Fallback chain confirmed. Now the failure paths — a skill must fail loudly, not silently.

[assistant] One more: the trigger phrase goes into SQL, and French phrases contain apostrophes.

[assistant] All robustness checks pass. Now rewriting `SKILL.md`, whose documented output still showed `/home/turbo` paths.

[assistant] All checks pass. Every remaining `/home/turbo` string is either the documented read-only SSD mount or the historical record of what was broken.

**Summary of the repair** (`/home/pamerys/.claude/skills/cli_skill_audit/`):

The skill produced *nothing* and reported success. Six causes, all confirmed by execution:

1. **Six hardcoded `/home/turbo` paths** (M1's home) — `mkdir: Permission non accordée`, no report, no DB.
2. **Silent failure, the worst one** — despite three fatal errors it printed `[driver] report : ...` and exited **rc=0**, announcing a file that did not exist.
3. **`run.sh` never called `driver.sh`** — it listed a nonexistent `/home/turbo/alkymia/scripts/audit/` and exited 0.
4. **`scan-secrets.sh` absent from M4** — verdict frozen at `rc=127`. Worse, its default repo list was also `/home/turbo/*`, so it would scan **zero repos and report "clean"**.
5. **Report name collision** — minute-granularity timestamps let two runs overwrite one file.
6. **Trigger coverage was wrong** — only the repo's 4 `run-*` skills were compared, ignoring the 47 in the user directory; this hid 40 uncovered skills.

Note on a concurrent event: a sibling agent installed its own `scan-secrets.sh` into `~/jarvis/bin/` at 09:42 during this session. My resolution cascade correctly prefers it over the copy I vendored into the skill; I verified the vendored fallback still works by redirecting `JARVIS_HOME`.

I deliberately did **not** run anything outbound — no network, no mail, no publish, 